# BotController Bridge

This software allows to control a Lego SPIKE Prime Hub over HTTP and BLE, assuming that the programs in the BotController Spike Prime Embedded project are deployed on the Hub.

The BotController Bridge connects to a REST-based queue that is defined in Pega Low Code. Then, the Bridge picks up and passes on the instructions.

Required packages:
- requests
- yaml
- bleak
- asyncio
