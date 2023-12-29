# BotController for Camera
Python program to run on Raspberry pi with a PiCamera installed.

The programm will poll rest endpoints for instructions and execute these if any are found.
The resultng fill will be uploaded through the standard Pega APIs.
You can use the launcher.sh script and add this to the start up actions

nano ~/.bashrc

Add this to the bottom:

sh /path/to/launcher.sh

Make sure you add the right values in the settings.yaml
