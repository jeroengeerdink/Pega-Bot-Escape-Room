import asyncio
from bleak import BleakScanner, BleakClient
import datetime

# Set the Raspberry Pi Zero's Bluetooth address
raspberry_pi_mac_address = "C2DCC8BB-7E76-96EA-323D-FFE053DCD116" #"B8:27:EB:F6:D2:E9"  # Replace with the actual MAC address of your Raspberry Pi Zero
#Device name: None, Address: 7BFA586A-8B10-8EB1-7DA1-BE6235420CFA
#Device name: None, Address: 508B083F-1DD3-2C27-0807-715DABB6C8F8
#Device name: None, Address: DF318844-F495-F7EF-AF44-89EC4FBE5476
#Controller B8:27:EB:F6:D2:E9 LegoCamera [default]

UART_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0" #"00001105-0000-1000-8000-00805f9b34fb"# "12345678-1234-5678-1234-56789abcdef0"
UART_RX_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
UART_TX_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1" #"12345678-1234-5678-1234-56789abcdef1" #"cbe16d48-9e9a-11ee-8c90-0242ac120002"

def handle_response(response):
    print(response)

async def receive_photo():
    # Scan for BLE devices
    scanner = BleakScanner()
    devices = await scanner.discover(10.0)
    device = None
    for d in devices:
        print(f"Device name: {d.name}, Address: {d.address}")
        if (d.name == "legocam"):
            device = d
    # Find the Raspberry Pi Zero device
    #device = next((d for d in devices if d.address == raspberry_pi_mac_address), None)
    #if not device:
    #    print("Raspberry Pi Zero not found.")
    #device = await BleakScanner.find_device_by_address(raspberry_pi_mac_address)
    #device = await BleakScanner.find_device_by_name("legocam")
  
    # Connect to the Raspberry Pi Zero
    #async with BleakClient() as client:

    print(device)
    client = BleakClient(device)

    await client.connect()
    print(client.services.characteristics)
    for key in client.services.characteristics:
        print(key, "->", client.services.characteristics[key])

    # Send the command to take a photo
    command = "photo"
    #await client.start_notify(UART_TX_CHAR_UUID, handle_response)
    nus = client.services.get_service(UART_SERVICE_UUID)
    rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)
    await client.write_gatt_char(UART_RX_CHAR_UUID, bytearray(command.encode()))

    # Receive the photo file
    photo_data = bytearray()
    print("Command sent")
    start = datetime.datetime.now()
    l = 0
    while True:
        data = await client.read_gatt_char(rx_char)
        if not data:
            break
        photo_data += data
        if (l != len(data)):
            l = len(data)
            print(len(data))

    finish = datetime.datetime.now()
    delta = finish - start
    print(len(photo_data))
    print(delta.seconds)

    # Save the photo to disk
    with open("captured_photo.jpg", "wb") as file:
        file.write(photo_data)
        print("Photo saved!")

    # Disconnect from the Raspberry Pi Zero
    await client.disconnect()

asyncio.run(receive_photo())