#!/usr/bin/python3
# -*- coding: UTF-8 -*-

## OSCcodec.py

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

# message.getValues()
import osc

def create_osc_message(self, title):
    '''Create an osc message:
        title is a string, must begining with "/"
            Example:
            - "/foo"
            - "/ping"
            - "/ham/egg"
            - "/*/egg"
        value is int or float or str but not list or dict.
    '''
    osc_msg = osc.Message(title)
    return osc_message

def add_value(self, msg, value):
    '''Add value to an osc message created with create_osc_message().'''
    msg.add(value)
    return msg

def decode_OSCmessage(msg):
    r = osc.Message.fromBinary(msg)
    a = r[0].getValues()
    b = r[0].getTypeTags()
    c = r[0].address
    decoded_msg = [c, b, a]
    print(decoded_msg)


# only to test this script standalone with pure data
if __name__ == "__main__":

    data = '/test\x00\x00\x00,i\x00\x00\x00\x00\x00\x87'
    data = '/test/rien\x00\x00,ifs\x00\x00\x00\x00\x00\x00\x00Q?\x8f\xd0\xd0toto\x00\x00\x00\x00'

    #r = osc._elementFromBinary(data)
    ##r = osc.Message.fromBinary(data)
    ##print(r[0], r[1])
##
    ##a = r[0].getValues()
    ##print(a)
##
    ##b = r[0].getTypeTags()
    ##print(b)
##
    ##c = r[0].address
    ##print("/{0}".format(c))
    decode_OSCmessage(data)
