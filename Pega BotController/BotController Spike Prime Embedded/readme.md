# Emdded program for Lego Robot

Code allows for the control of a Spike Prime robot ver Bluetooth using a simple protcol.
Make sure tha spike prime is flashed with pybricks > https://pybricks.com/
You can then upload the code using > https://code.pybricks.com/

Basic instructions chave the following structure

[action]>[param1]|[param2]|param....]

## PegaController

Controlls communication with the BotController Bridge program passing any instructions to the RobotController

## RobotController

Takes the instructions from the PegaController and executues them using the pybricks interfaces.

