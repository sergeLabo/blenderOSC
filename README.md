## blenderOSC

Send and receive OSC message in Blender Game Engine with python 3.4, on UDP,

easily, in an example.

### Content

class Receive only to receive and decode

class Send to send binary osc message or encoded string

class Client to send and receive, but without decoding.


### Limitation
String are latin-1 encoded and decoded.

    ISO 8859-1 = ISO/CEI 8859-1 = Latin-1

To receive or send unicode string, don't use OSC.

Use listen_unicode() in send_receive.py to receive UDP data without OSC.

Send with socket.sendto(data, address)

and data = "your unicode string".encode('utf-8')

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

test.py run in subprocess:
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
