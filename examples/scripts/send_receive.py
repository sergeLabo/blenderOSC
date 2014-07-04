#!/usr/bin/python3
# -*- coding: UTF-8 -*-

## send_receive.py

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

import socket
try:
    import osc
except:
    import scripts.osc

#import OSCcodec


class Receive:
    '''.'''
    def __init__(self, ip, port, buffer_size, verbose=False):
        '''Plug a socket.'''
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.verb = verbose
        self.data = None


        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind((self.ip, self.port))
            self.sock.setblocking(0)
            self.sock.settimeout(0.10)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
            if self.verb:
                print('Plug : IP = {} Port = {} Buffer Size = {}'.
                      format(ip, port, buffer_size))
        except:
            if self.verb:
                print('No connected on {0}:{1}'.format(self.ip, self.port))

    def listen(self):
        '''Return decoded OSC data, or None.'''
        try:
            raw_data = self.sock.recv(self.buffer_size)
            if self.verb:
                print("Receive from {0}:{1} : {2}".format(self.ip,
                                                self.port, raw_data))
            self.convert_data(raw_data)
        except:
            if self.verb:
                print('Nothing from {0}:{1}'.format(self.ip, self.port))
        return self.data

    def convert_data(self, raw_data):
        try:
            self.data = raw_data
            if self.verb:
                print("Decoded OSC message: {0}".format(self.data))
        except:
            if self.verb:
                print('Impossible to decode {0}'.format(raw_data))

class Send():
    '''Create your OSC messge with osc,
    example:
        msg = osc.Message("/test/rien")
        msg.add(120)
        msg.add(1.12356)
        msg.add("toto")
    '''

    def __init__(self, verbose=True):
        '''Create an UDP socket.'''
        self.verb = verbose
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def osc_sendto(self, msg, ip, port):
        '''Send msg to ip:port
        msg is an OSC message create with create_osc_message()'''
        msg_bin = msg.toBinary()
        self.sock.sendto(msg_bin, (ip, port))
        if self.verb:
            print("OSC message sended: {0}".format(msg_bin))

# only to test this script standalone with pure data
if __name__ == "__main__":
    from time import sleep

    buffer_size = 1024

    ip_in = "127.0.0.1"
    port_in = 8000

    ip_out = "127.0.0.1"
    port_out = 9000

    my_receiver = Receive(ip_in, port_in, buffer_size, verbose=True)

    my_sender = Send(verbose=True)

    a = 0
    while True:
        a += 1
        sleep(0.01)

        data = my_receiver.listen()

        msg = osc.Message("/test/rien")
        msg.add(a)
        msg.add(1.12356)
        msg.add("toto")
        my_sender.osc_sendto(msg, ip_out, port_out)
