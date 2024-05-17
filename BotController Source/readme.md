# Project python sources
These folders contain teh different Python sources for the various components of the project.

## Bot to Pega Bridge [Python]
This component acts as a bridge to transfer instructions between an Internet-connected laptop (or other  device) and the Lego robot Hub. The bridge transfers the instructions: either from the device to the Hub (first over HTTP and then via BLE); or from the Hub to the device (first via BLE and then over HTTP).

## Camera Embedded [Python]
This component runs on a Raspberry Pi device that has a camera, and therefore allows Pega Low Code to take photos. The device requires an Internet connection to work.

## Spike Prime Embedded [Python]
This component uses pybricks to control a Lego robot that is based on a SPIKE Prime multi-port Hub. To use pybricks, you must first flash pybricks to the Hub.
