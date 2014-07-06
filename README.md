## blenderOSC

Send and receive OSC message in Blender Game Engine with python 3.4, on UDP.

easily, in an example.

### Requirements

* python3.4 and more
* socket standard module
* pyOSCcodec: https://github.com/sergeLabo/pyOSCcodec
* blender 2.69 and more


### Installation

Tested on:
    Linux Mint 17

    Ubuntu 14.04

You must install pd-extended

for example from

https://launchpad.net/~eighthave/+archive/pd-extended/+files/pd-extended_0.43.4-1%7Etrusty1_i386.deb

### Running the Tests

Run in terminal
    python3 test.py

test launch:
- send_receive.py
- pd-extended the patch OSC-PureData-Blender-xy.pd
- blender

try:
- connect in pure data
- [P] over Blender 3D View
- Move x y slider

### Credits
Thanks to:
* Labomedia


### License
Skandal is released under the GENERAL PUBLIC LICENSE Version 2, June 1991.
See the bundled LICENSE file for details.

