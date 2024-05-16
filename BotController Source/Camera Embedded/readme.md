# BotController for Camera
This Python program runs on a Raspberry Pi that has an installed PiCamera.

The program polls REST endpoints for instructions and executes any incoming instructions.
The result is uploaded through the standard Pega APIs.

You can use the launcher.sh script and add this to the start-up actions.
nano ~/.bashrc

Add this to the bottom:
sh /path/to/launcher.sh

Make sure that you add the correct values to the settings.yaml file.
