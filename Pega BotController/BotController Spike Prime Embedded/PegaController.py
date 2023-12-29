from pybricks.hubs import PrimeHub
from pybricks.tools import wait
from pybricks.parameters import Color, Button

# Standard MicroPython modules
from usys import stdin, stdout
from uselect import poll

# Custom Robot Controller
import RobotController

hub = PrimeHub()

# Optional: Register stdin for polling. This allows
# you to wait for incoming data without blocking.
keyboard = poll()
keyboard.register(stdin)

def main():
    keyboard = poll()
    keyboard.register(stdin)

    RobotController.setup()

    hub.light.on(Color.RED)
    hub.display.text("ok")
    cmd = b""
    stdout.write("Hello")
    stdout.flush()
    hub.light.on(Color.GREEN)
    while True:
        while not keyboard.poll(0):
            pressed = []
            pressed = hub.buttons.pressed()
            if Button.LEFT in pressed:
                RobotController.tightenGrabber()
            wait(10)
        char = b""
        try:
            char = stdin.buffer.read(1)
            if char == b"\r":
                param = str(cmd, "utf-8")
                response = RobotController.handleCommand(param)
                stdout.write("OK" + ">" + response)
                stdout.flush()
                cmd = b""
            elif char != b"":
                cmd = cmd + char
        except Exception as e:
            stdout.buffer.write(bytearray(str(e)))
            cmd = b""
            hub.display.text("Error")

if __name__ == '__main__':
    main()