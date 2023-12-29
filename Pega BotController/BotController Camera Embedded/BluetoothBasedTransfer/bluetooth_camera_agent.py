#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

import picamera

import array
from gi.repository import GLib
try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject
import sys

import io
from random import randint

mainloop = None
device_manager = None

camera = picamera.PiCamera()

BLUEZ_SERVICE_NAME = 'org.bluez'
DEVICE_IFACE = 'org.bluez.Device1'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
DBUS_OM_IFACE =      'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE =    'org.freedesktop.DBus.Properties'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE =    'org.bluez.GattCharacteristic1'
GATT_DESC_IFACE =    'org.bluez.GattDescriptor1'

LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'

OBEX_SERVICE_UUID = '00001105-0000-1000-8000-00805f9b34fb'
OBEX_CHARACTERISTIC_UUID = '00001106-0000-1000-8000-00805f9b34fb'

class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.freedesktop.DBus.Error.InvalidArgs'

class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotSupported'

class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotPermitted'

class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.InvalidValueLength'

class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.Failed'


class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.add_service(PhotoService(bus, 0))
        self.add_service(ObexService(bus, 1))

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        print('GetManagedObjects')

        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()

        return response

class DeviceManager(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/org/bluez/example/devicemanager'
        self.bus = bus
        dbus.service.Object.__init__(self, bus, self.path)

    @dbus.service.signal(BLUEZ_SERVICE_NAME, signature='o')
    def DeviceConnected(self, device_path):
        pass

    @dbus.service.signal(BLUEZ_SERVICE_NAME, signature='o')
    def DeviceDisconnected(self, device_path):
        pass

    @dbus.service.method(BLUEZ_SERVICE_NAME, in_signature='o')
    def ConnectDevice(self, device_path):
        self.DeviceConnected(device_path)

    @dbus.service.method(BLUEZ_SERVICE_NAME, in_signature='o')
    def DisconnectDevice(self, device_path):
        self.DeviceDisconnected(device_path)

    def start(self):
        self.bus.add_signal_receiver(
            self.device_connected_cb,
            dbus_interface=BLUEZ_SERVICE_NAME,
            signal_name='DeviceConnected'
        )
        self.bus.add_signal_receiver(
            self.device_disconnected_cb,
            dbus_interface=BLUEZ_SERVICE_NAME,
            signal_name='DeviceDisconnected'
        )

    def device_connected_cb(self, device_path):
        self.DeviceConnected(device_path)

    def device_disconnected_cb(self, device_path):
        self.DeviceDisconnected(device_path)

    def get_device_address(self, device_path):
        device_props = dbus.Interface(
            self.bus.get_object(BLUEZ_SERVICE_NAME, device_path),
            DBUS_PROP_IFACE
        )
        props = device_props.GetAll(DEVICE_IFACE)
        return props['Address']

class Service(dbus.service.Object):
    """
    org.bluez.GattService1 interface implementation
    """
    PATH_BASE = '/org/bluez/example/service'

    def __init__(self, bus, index, uuid, primary):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_SERVICE_IFACE: {
                        'UUID': self.uuid,
                        'Primary': self.primary,
                        'Characteristics': dbus.Array(
                                self.get_characteristic_paths(),
                                signature='o')
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristic_paths(self):
        result = []
        for chrc in self.characteristics:
            result.append(chrc.get_path())
        return result

    def get_characteristics(self):
        return self.characteristics

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_SERVICE_IFACE]


class Characteristic(dbus.service.Object):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_CHRC_IFACE: {
                        'Service': self.service.get_path(),
                        'UUID': self.uuid,
                        'Flags': self.flags,
                        'Descriptors': dbus.Array(
                                self.get_descriptor_paths(),
                                signature='o')
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptor_paths(self):
        result = []
        for desc in self.descriptors:
            result.append(desc.get_path())
        return result

    def get_descriptors(self):
        return self.descriptors

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_CHRC_IFACE]

    @dbus.service.method(GATT_CHRC_IFACE,
                        in_signature='a{sv}',
                        out_signature='ay')
    def ReadValue(self, options):
        print('Default ReadValue called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print('Default WriteValue called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        print('Default StartNotify called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        print('Default StopNotify called, returning error')
        raise NotSupportedException()

    @dbus.service.signal(DBUS_PROP_IFACE,
                         signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass


class Descriptor(dbus.service.Object):
    """
    org.bluez.GattDescriptor1 interface implementation
    """
    def __init__(self, bus, index, uuid, flags, characteristic):
        self.path = characteristic.path + '/desc' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.chrc = characteristic
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_DESC_IFACE: {
                        'Characteristic': self.chrc.get_path(),
                        'UUID': self.uuid,
                        'Flags': self.flags,
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_DESC_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_DESC_IFACE]

    @dbus.service.method(GATT_DESC_IFACE,
                        in_signature='a{sv}',
                        out_signature='ay')
    def ReadValue(self, options):
        print ('Default ReadValue called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_DESC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print('Default WriteValue called, returning error')
        raise NotSupportedException()

class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/advertisement'

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = None
        self.manufacturer_data = None
        self.solicit_uuids = None
        self.service_data = None
        self.local_name = None
        self.include_tx_power = False
        self.data = None
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        properties = dict()
        properties['Type'] = self.ad_type
        if self.service_uuids is not None:
            properties['ServiceUUIDs'] = dbus.Array(self.service_uuids,
                                                    signature='s')
        if self.solicit_uuids is not None:
            properties['SolicitUUIDs'] = dbus.Array(self.solicit_uuids,
                                                    signature='s')
        if self.manufacturer_data is not None:
            properties['ManufacturerData'] = dbus.Dictionary(
                self.manufacturer_data, signature='qv')
        if self.service_data is not None:
            properties['ServiceData'] = dbus.Dictionary(self.service_data,
                                                        signature='sv')
        if self.local_name is not None:
            properties['LocalName'] = dbus.String(self.local_name)
        if self.include_tx_power:
            properties['Includes'] = dbus.Array(["tx-power"], signature='s')

        if self.data is not None:
            properties['Data'] = dbus.Dictionary(
                self.data, signature='yv')
        return {LE_ADVERTISEMENT_IFACE: properties}

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service_uuid(self, uuid):
        if not self.service_uuids:
            self.service_uuids = []
        self.service_uuids.append(uuid)

    def add_solicit_uuid(self, uuid):
        if not self.solicit_uuids:
            self.solicit_uuids = []
        self.solicit_uuids.append(uuid)

    def add_manufacturer_data(self, manuf_code, data):
        if not self.manufacturer_data:
            self.manufacturer_data = dbus.Dictionary({}, signature='qv')
        self.manufacturer_data[manuf_code] = dbus.Array(data, signature='y')

    def add_service_data(self, uuid, data):
        if not self.service_data:
            self.service_data = dbus.Dictionary({}, signature='sv')
        self.service_data[uuid] = dbus.Array(data, signature='y')

    def add_local_name(self, name):
        if not self.local_name:
            self.local_name = ""
        self.local_name = dbus.String(name)

    def add_data(self, ad_type, data):
        if not self.data:
            self.data = dbus.Dictionary({}, signature='yv')
        self.data[ad_type] = dbus.Array(data, signature='y')

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        print('GetAll')
        if interface != LE_ADVERTISEMENT_IFACE:
            raise InvalidArgsException()
        print('returning props')
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE,
                         in_signature='',
                         out_signature='')
    def Release(self):
        print('%s: Released!' % self.path)


class PhotoAdvertisement(Advertisement):

    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid('180D')
        self.add_service_uuid('180F')
        self.add_manufacturer_data(0xffff, [0x00, 0x01, 0x02, 0x03])
        self.add_service_data('9999', [0x00, 0x01, 0x02, 0x03, 0x04])
        self.add_local_name('PhotoAdvertisement')
        self.include_tx_power = True
        self.add_data(0x26, [0x01, 0x01, 0x00])


class PhotoService(Service):
    """
    Dummy test service that provides characteristics and descriptors that
    exercise various API functionality.

    """
    PHOTO_SVC_UUID = '12345678-1234-5678-1234-56789abcdef0'

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.PHOTO_SVC_UUID, True)
        self.add_characteristic(PhotoCharacteristic(bus, 0, self))
        #self.add_characteristic(TestEncryptCharacteristic(bus, 1, self))
        #self.add_characteristic(TestSecureCharacteristic(bus, 2, self))

class PhotoCharacteristic(Characteristic):
    """
    Dummy test characteristic. Allows writing arbitrary bytes to its value, and
    contains "extended properties", as well as a test descriptor.

    """
    TEST_CHRC_UUID = '12345678-1234-5678-1234-56789abcdef1'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.TEST_CHRC_UUID,
                ['read', 'write', 'writable-auxiliaries'],
                service)
        self.value = []
        self.activated = False
        self.offset = 0
        self.add_descriptor(PhotoDescriptor(bus, 0, self))
        self.add_descriptor(
                CharacteristicUserDescriptionDescriptor(bus, 1, self))

    #def ReadValue(self, options):
    #    print("Read > " + self.activated)
    #    if (self.activated):
    #        print("Taking photo")
    #        photo = capture_photo()
    #        print(photo)
    #        return photo
    #    return [dbus.Byte('T'), dbus.Byte('e'), dbus.Byte('s'), dbus.Byte('t')]

    def ReadValue(self, options):
        if (self.activated):
            return capture_photo()
        else:
            chunk_size = 500  # Adjust the chunk size to match the MTU size of your BLE connection
            if 'mtu' in options:
                mtu = options['mtu']
                chunk_size = mtu - 4  # Subtract 4 bytes for the ATT header
                print(chunk_size)
            result = []

            if (self.offset < len(self.value)):
                chunk = self.value[self.offset:self.offset+chunk_size]
                result.extend(chunk)
                self.offset += chunk_size
            else:
                print(len(self.value))
                self.value = []
            return result


    def WriteValue(self, value, options):
        action = bytes(value).decode()
        print("Action > " + action)
        if (action == "on"):
            self.activated = True
        if (action == "off"):
            self.activated = False
        if (action == "photo"):
            self.value = capture_photo()


    def GetAll(self, interface):
        if interface == GATT_CHRC_IFACE:
            properties = self.get_properties()[GATT_CHRC_IFACE]
            properties['MTU'] = dbus.UInt16(1024)  # Set the desired MTU size
            return properties
        else:
            raise InvalidArgsException()


class PhotoDescriptor(Descriptor):
    """
    Dummy test descriptor. Returns a static value.

    """
    TEST_DESC_UUID = '12345678-1234-5678-1234-56789abcdef2'

    def __init__(self, bus, index, characteristic):
        Descriptor.__init__(
                self, bus, index,
                self.TEST_DESC_UUID,
                ['read', 'write'],
                characteristic)

    def ReadValue(self, options):
        return [
                dbus.Byte('T'), dbus.Byte('e'), dbus.Byte('s'), dbus.Byte('t')
        ]


class ObexCharacteristic(Characteristic):
    """
    Characteristic for sending a file over OBEX.
    """

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            OBEX_CHARACTERISTIC_UUID,
            ['read', 'write'],
            service)
        self.file_data = []

    def ReadValue(self, options):
        if self.file_data:
            return self.file_data
        else:
            raise FailedException("No file data available")

    def WriteValue(self, value, options):
        action = bytes(value).decode()
        print("OBEX Action > " + action)
        if (action == "on"):
            self.activated = True
        if (action == "off"):
            self.activated = False
        if (action == "photo"):
            self.file_data = capture_photo()
            print(len(self.file_data))
            device_path = self.service.get_path() #.replace('/service', '')
            print(self.service.get_path())
            print(device_manager)
            devices = list_connected_devices()
            for device in devices:
                print("Connected device:", device)
            address = "88:66:5A:33:78:8E" #device_manager.get_device_address(device_path)
            print(address)
            print("0000")
            send_file_via_obex(self.file_data, address=address)

class ObexService(Service):
    """
    Service that provides the OBEX characteristic.
    """

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, OBEX_SERVICE_UUID, True)
        self.add_characteristic(ObexCharacteristic(bus, 0, self))


class CharacteristicUserDescriptionDescriptor(Descriptor):
    """
    Writable CUD descriptor.

    """
    CUD_UUID = '2901'

    def __init__(self, bus, index, characteristic):
        self.writable = 'writable-auxiliaries' in characteristic.flags
        self.value = array.array('B', b'This is a characteristic for testing')
        self.value = self.value.tolist()
        Descriptor.__init__(
                self, bus, index,
                self.CUD_UUID,
                ['read', 'write'],
                characteristic)

    def ReadValue(self, options):
        return self.value

    def WriteValue(self, value, options):
        if not self.writable:
            raise NotPermittedException()
        self.value = value

def register_app_cb():
    global app
    global device_manager
    print('GATT application registered')
    app_path = app.get_path()
    device_manager.ConnectDevice(app_path)

def device_connected_cb(device_path):
    print('GATT connection established')
    conn_props = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, device_path),
        DBUS_PROP_IFACE)
    conn_props.Set(GATT_CHRC_IFACE, 'MTU', dbus.UInt16(2048))  # Set the desired MTU size

def device_disconnected_cb(device_path):
    print('GATT connection disconnected')
    mainloop.quit()

def register_app_error_cb(error):
    print('Failed to register application: ' + str(error))
    mainloop.quit()


def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if GATT_MANAGER_IFACE in props.keys():
            return o

    return None

def register_ad_cb():
    print('Advertisement registered')


def register_ad_error_cb(error):
    print('Failed to register advertisement: ' + str(error))
    mainloop.quit()

def capture_photo():
    # Capture a photo into a stream
    stream = io.BytesIO()
    camera
    camera.capture(stream, format='jpeg')
    stream.seek(0)
    st = stream.read()
    # Send the photo over Bluetooth
    photo = dbus.Array([dbus.Byte(b) for b in st])
    print("Photo taken")
    return st
    #return []


def send_file_via_obex(file_data, address):
    # Connect to the OBEX service
    print("1111")
    bus = dbus.SystemBus()
    print("1112")
    list_services()
    manager = bus.get('org.bluez.obex', '/org/bluez/obex')
    print("1113")
    session = manager.CreateSession({'Target': address})
    print("1114")
    obex = bus.get('org.bluez.obex', session)

    print("AAAA")
    # Create a new OBEX transfer object
    transfer = obex.CreateTransfer()

    # Set the file data as the transfer data
    transfer.Push(file_data)
    print("BBBB")

    # Start the transfer
    transfer.Start()
    print("CCCC")

    # Wait for the transfer to complete
    loop = GLib.MainLoop()
    loop.run()

    print("DDDD")

    # Clean up the transfer
    transfer.Destroy()
    obex.Release()

def list_connected_devices():
    bus = dbus.SystemBus()
    manager_obj = bus.get_object("org.bluez", "/")
    manager_iface = dbus.Interface(manager_obj, "org.freedesktop.DBus.ObjectManager")
    objects = manager_iface.GetManagedObjects()

    connected_devices = []
    for path, interfaces in objects.items():
        if "org.bluez.Device1" in interfaces:
            device_props = objects[path]["org.bluez.Device1"]
            connected = device_props.get("Connected", False)
            if connected:
                connected_devices.append(device_props["Address"])

    return connected_devices

def list_services():
    bus = dbus.SystemBus()
    manager_obj = bus.get_object("org.bluez", "/")
    manager_iface = dbus.Interface(manager_obj, "org.freedesktop.DBus.ObjectManager")
    objects = manager_iface.GetManagedObjects()

    for path, interfaces in objects.items():
        print("Object Path:", path)
        print("Interfaces:", interfaces)
        print()

def main():
    global mainloop
    global device_manager
    global service_manager
    global bus
    global app

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    adapter = find_adapter(bus)
    if not adapter:
        print('GattManager1 interface not found')
        return

    service_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            GATT_MANAGER_IFACE)
    
    device_manager = DeviceManager(bus)
    device_manager.start()
    
    ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                LE_ADVERTISING_MANAGER_IFACE)

    Photo_advertisement = PhotoAdvertisement(bus, 0)


    ad_manager.RegisterAdvertisement(Photo_advertisement.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)

    app = Application(bus)

    mainloop = GLib.MainLoop() #GObject.MainLoop()


    #service_manager.RegisterApplication(app.get_path(), {},
    #                                reply_handler=register_app_cb,
    #                                error_handler=register_app_error_cb)
    print('Registering GATT application...')
    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)
    
    mainloop.run()

if __name__ == '__main__':
    camera.resolution = (1024, 768)
    main()

