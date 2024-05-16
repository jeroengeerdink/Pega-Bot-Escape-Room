# Pega Bot

This set of software components extends Pega Low Code with the ability to control a Lego robot and other items, such as a camera.

There are four main components:

## BotController Bridge
This component acts as a bridge to transfer instructions between an Internet-connected laptop (or other  device) and the Lego robot Hub. The bridge transfers the instructions: either from the device to the Hub (first over HTTP and then via BLE); or from the Hub to the device (first via BLE and then over HTTP).

## BotController Camera Embedded
This component runs on a Raspberry Pi device that has a camera, and therefore allows Pega Low Code to take photos. The device requires an Internet connection to work.

## BotController Spike Prime Embedded
This component uses pybricks to control a Lego robot that is based on a SPIKE Prime multi-port Hub. To use pybricks, you must first flash pybricks to the Hub.

## Pega RAPs
These Rule Application Products contain teh Pega configuration to make the Lego Bot controllable from App studio.
