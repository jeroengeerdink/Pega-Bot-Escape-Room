# Embedded program for Lego Robot

This code allows to control a Spike Prime-based robot via Bluetooth by using a simple protocol.
Make sure that the SPIKE Prime Hub is flashed with pybricks > https://pybricks.com/
You can then upload robot-specific code to the Hub by using > https://code.pybricks.com/

The instructions that define the behavior of the robot have the following structure:

[action]>[param1]|[param2]|param....]

## PegaController

This code manages communications with the BotController Bridge program by parsing and then passing any instructions to the RobotController

## RobotController

This code: (1) defines the setup of the Lego robot. For example, it specifies which motors and sensors are connected to which port on the Hub. In addition, it defines the size of elements of the robot drive-base.
(2) parses instructions into commands and parameters.  
(3) defines the behavior of the robot by defining the required steps in routines, and passing the steps to the pybricks API interface. For example, routines allow for the robot to open, close, and tighten its grabber hand. Other routines allow the robot to check sensors for colors or collisions, to drive as required, to search for an object, and to dance.

