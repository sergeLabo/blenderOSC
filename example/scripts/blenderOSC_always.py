#!/usr/bin/python3
# -*- coding: UTF-8 -*-

## blenderOSC_always.py

#############################################################################
# Copyright (C) Labomedia July 2014
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franproplin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#############################################################################

'''
This script run at all frame.
'''

import random
from bge import logic as gl

# Listen every frame
gl.data = gl.my_receiver.get_data()

# Get x, y in data OSC message
if gl.data:
    if "/pos-X" in gl.data:
        gl.x = gl.data[2]
    if "/pos-Y" in gl.data:
        gl.y = gl.data[2]
# if not gl.data, gl.x and gl.y don't change, the cube is already at the same place

# Move the Cube
controller = gl.getCurrentController()
owner = controller.owner
owner.localPosition = [0.3*gl.x, 0.3*gl.y, 0]

# Send
res = 30*random.random() - 15  # from 15 to 15
gl.my_sender.simple_send_to("/blender/x", res, (gl.ip_out, gl.port_out))
