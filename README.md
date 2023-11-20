# PegaBotController

This software allows to control a Lego Spike Prime over Bluetooth using a simple protocol, assuming the PegaBotEmbed project is deployed on it.

The Controller will connect to a Rest based queue defined in Pega to pick up and pass on instructions.

Required packages:
- requests
- yaml
- bleak
- asyncio
