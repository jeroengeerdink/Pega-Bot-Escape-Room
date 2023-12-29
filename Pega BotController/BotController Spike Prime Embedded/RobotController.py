from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor, UltrasonicSensor, ForceSensor
from pybricks.parameters import Button, Color, Direction, Port, Side, Stop
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch
from usys import stdin, stdout


STEP_UNIT = 100
BLACK_REFLECTION = 20
SEARCH_RANGE = 800
SEARCH_ANGLE = 40
SEARCH_CLOSENESS = 80

hub = PrimeHub()

left_motor=Motor(Port.D,Direction.COUNTERCLOCKWISE) 
right_motor=Motor(Port.C)
sensor = ColorSensor(Port.E)
claw_motor=Motor(Port.F)
eyes = UltrasonicSensor(Port.B)
drive_base=DriveBase(left_motor,right_motor,wheel_diameter=56,axle_track=112)

hub.speaker.volume(100)
hub.display.orientation(Side.BOTTOM)

shortestDistance = SEARCH_RANGE
shortestAngle = 0

def setup():
    hub.speaker.volume(100)
    hub.display.orientation(Side.BOTTOM)

shortestDistance = SEARCH_RANGE
shortestAngle = 0 

# commands follow the following structure
# [action] > [param] | [param]
# e.g. drive>50

def handleCommand(cmd):
    response = ""
    cmdParts = cmd.split(">")
    action = cmdParts[0]
    try:
        params = cmdParts[1].split("|")
    except IndexError as e:
        params = []
    if action == "drive":
        if params[0] == "until":
            driveUntil(params[1], params[2])
        else:
            try:
                drive(int(params[0]), params[1])
            except IndexError:
                drive(int(params[0]), "false")
    elif action == "turn":
        turn(int(params[0]))
    elif action == "display":
        hub.display.text(params[0])
    elif action == "searchandgrab":
        try:
            response = searchAndGrab(int(params[0]), int(params[1]))
        except IndexError:
            response = searchAndGrab(SEARCH_RANGE, SEARCH_ANGLE)
    elif action == "releasegrabber":
        release()
    elif action == "dance":
        dance()
    elif action == "setting":
        applySettings(params)
    
    return response

def applySetting(params):
    for p in params:
        keyValue = p.split("=")
        if keyValue[0] == "volume":
            try:
                hub.speaker.volume(int(keyValue[1]))
            except IndexError:
                pass
                
def checkSensorsForCollision():
    if sensor.reflection() <= BLACK_REFLECTION and sensor.color(True) == Color.NONE:
        sound_gameover()
        stdout.write("linedetected")
        stdout.flush()
        return True
    return False

def checkSensors(color):
    if color == "white" and sensor.color(True) == Color.WHITE:
        return True
    elif color == "red" and sensor.color(True) == Color.RED:
        return True
    elif color == "yellow" and sensor.color(True) == Color.YELLOW:
        return True
    elif color == "blue" and sensor.color(True) == Color.BLUE:
        return True
    elif color == "green" and sensor.color(True) == Color.GREEN:
        return True
    return False


def drive(steps, ignore="false"):
    drive_base.straight(steps * STEP_UNIT, wait=False)
    while not drive_base.done():
        wait(10)
        if ignore != "true":
            if checkSensorsForCollision():
                drive_base.stop()
                return

def driveUntil(color, ignore="false"):
    drive_base.straight(100 * STEP_UNIT, wait=False)
    while not drive_base.done():
        wait(10)
        if checkSensors(color):
            drive_base.stop()
            return
        if ignore != "true":
            if checkSensorsForCollision():
                drive_base.stop()
                return

def turn(degrees):
    drive_base.turn(degrees)

def grabberOpen():
    claw_motor.run_time(40, 1500)

def grabberClose():
    claw_motor.run_time(-44, 1500)

def grab():
    grabberOpen()
    turn(15)
    drive_base.straight(70, wait=True)
    grabberClose()
    turn(-15)
    drive_base.straight(-70, wait=True)

def tightenGrabber():
    claw_motor.run_time(-20, 1500)

def release():
    grabberOpen()
    drive_base.straight(-70, wait=True)
    grabberClose()

def searchObject(r):
    global shortestDistance
    global shortestAngle
    SEARCH_ANGLE = r
    found = False
    for i in range(SEARCH_ANGLE):
        turn(1)
        if eyes.distance() < shortestDistance:
            shortestDistance = eyes.distance()
            shortestAngle = i
    turn(-30)
    for i in range(SEARCH_ANGLE):
        turn(-1)
        if eyes.distance() < shortestDistance:
            shortestDistance = eyes.distance()
            shortestAngle = i * -1
    turn(30)
    if shortestDistance < SEARCH_RANGE:
        if shortestDistance > SEARCH_CLOSENESS:
            turn(shortestAngle)
            drive_base.straight(shortestDistance-SEARCH_CLOSENESS , wait=True)
            return True
            #searchObject()
        else:
            return True
    return False    

def searchAndGrab(d, r):
    global shortestDistance
    global shortestAngle
    shortestDistance = d
    shortestAngle = 0
    eyes.lights.on()
    if searchObject(r):
        sound_success()
        grab()
        drive_base.straight(-1 * (shortestDistance-SEARCH_CLOSENESS) , wait=True)
        turn(-1 * shortestAngle)
        eyes.lights.off()
        return "success"
    else:
        sound_unsuccessful()
        eyes.lights.off()
        return "notfound"

def sound_gameover():
    hub.speaker.play_notes([
        "E4/8", "E4/8", "E4/8", "C4/8", "G4/8", "E3/4", "G3/4", "C4/2"
    ], tempo=120)

def sound_success():
    hub.speaker.play_notes([
        "E5/8", "E5/8", "E5/8", "C5/8", "G5/8", "E4/4", "G4/4", "C5/2"
    ], tempo=120)

def sound_unsuccessful():
    hub.speaker.play_notes([
        "C4/4", "B3/8", "A3/8", "G3/2"
    ], tempo=120)

def sound_party():
    hub.speaker.play_notes([
        "G4/8", "G4/8", "G4/8", "G4/8", "A4/8", "A4/8", "A4/8", "A4/8",
        "B4/8", "B4/8", "B4/8", "B4/8", "C5/8", "C5/8", "C5/8", "C5/8",
        "D5/8", "D5/8", "D5/8", "D5/8", "E5/8", "E5/8", "E5/8", "E5/8",
        "F#5/8", "F#5/8", "F#5/8", "F#5/8", "G5/4"
    ], tempo=120)

def sound_flirt():
    hub.speaker.play_notes([
        "G4/8", "A4/8", "B4/8", "A4/8", "G4/8",
        "E4/8", "D4/8", "E4/8", "F#4/8", "G4/2"
    ], tempo=120)

def dance():
    sound_flirt()
    drive(1)
    drive(-1)
    turn(360)
    drive(-1)
    drive(1)

if __name__ == '__main__':
    #print(sensor.reflection())
    #print(sensor.color(True))
    #grab()
    #grabberOpen()
    #handleCommand("drive>1|true")
    #grabberClose()
    #print(eyes.distance())
    #handleCommand("drive>until|blue|false")
    #handleCommand("display>Script")
    #handleCommand("drive>1|true")
    #handleCommand("turn>90")
    #handleCommand("drive>-3|false")
    #release()
    #handleCommand("turn>-180")
    #print(searchObject())
    #tightenGrabber()
    #searchAndGrab()
    #handleCommand("searchandgrab>800|40")
    #dance()
    #sound_flirt()
    pass