import asyncio
from bleak import BleakScanner, BleakClient
import time

device_address = "4BE0413D-EEC3-5108-695E-00408FD59605"

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

class LegoControllerException(Exception):
    def __init__(self, type):
        self.type = type

    def getData(self):
        return {"type": self.type}

class LegoController:
    def __init__(self, name, onReady):
        self.name = name
        self.ready = False
        self.onReady = onReady
        self.processing = False
        self.response = ""
        #self.device = self.backend.connect(device_address)

    async def connect(self):
        device = await BleakScanner.find_device_by_name(self.name)
        self.client = BleakClient(device, disconnected_callback=self.handle_disconnect)
        print(self.client)
        await self.client.connect()
        await self.client.start_notify(UART_TX_CHAR_UUID, self.handle_response)
        self.nus = self.client.services.get_service(UART_SERVICE_UUID)
        self.rx_char = self.nus.get_characteristic(UART_RX_CHAR_UUID)
        self.ready = True
        self.onReady()
        self.event = ""
        self.connected = False
        print("Start the program on the hub now with the button.")
        while self.connected == False:
            await asyncio.sleep(0.5)
        print("Connection established.")

    def handle_disconnect(self):
        print("Hub was disconnected.")

    def handle_response(self, _, data: bytearray):
        response = str(data, encoding='utf-8')
        print("Received:", response)
        if response.startswith("OK"):
            self.response = response[3:]
            self.processing = False
        elif response == "linedetected":
            self.processing = False
            self.event = "collision"
        elif response == "Hello":
            self.connected = True

    async def send(self, data):
        print(data)
        data = data + "\r"
        await self.client.write_gatt_char(self.rx_char, data.encode(encoding = 'UTF-8'))
    
    async def wait(self):
        while self.processing:
            await asyncio.sleep(0.5)

    async def execute(self, action, parameters):
        self.event = ""
        self.response = ""
        action = action.lower()
        self.processing = True
        await self.send(action+">"+parameters)
        await self.wait()
        if self.event != "":
            raise LegoControllerException(self.event)
    
async def main():
    def callBack():
        print("Ready")
    controller = LegoController("Pega One", callBack)
    await controller.connect()
    time.sleep(5)
    await controller.execute("drive","5")
    print(controller.event)
    #controller.wait()
    await controller.execute("drive","5")
    print(controller.event)
    #controller.wait()
    await controller.execute("turn","90")
    print(controller.event)
    #controller.wait()
    time.sleep(5)


if __name__ == '__main__':
    asyncio.run(main()) 
    