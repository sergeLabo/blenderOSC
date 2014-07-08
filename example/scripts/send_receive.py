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


'''
Send class send UDP OSC message,
Receive class receive OSC message.
Build with python3 socket standard module.


OSC message are created and decoded with OSCcodec.py in pyOSCcodec at
https://github.com/sergeLabo/pyOSCcodec

pyOSCcodec is a part of OSC.py, from
https://gitorious.org/pyosc/devel/source/6aaf78b0c1e89942a9c5b1952266791b7ae16012:

See documentation in send_receive.html.

The aim of this script is to be used in the
Blender Game Engine in python script.

Blender Game engine don't accept thread, twisted, socketserver, asyncio ...

String are latin-1 encoded and decoded.

'''


import socket
try:
    # to run standalone
    from OSCcodec import OSCMessage, decodeOSC
except:
    # to run in blender scripts directory
    from scripts.OSCcodec import OSCMessage, decodeOSC


class Receive:
    '''Receive, decode OSC Message with a socket .'''
    def __init__(self, ip, port, buffer_size=1024, verbose=False):
        '''Plug an UDP socket.
        ip example: "localhost", "127.0.0.1", "10.0.0.100"
        port = integer
        buffer_size = integer, used to clear out the buffer at each reading
        verbose = True is very verbose in terminal
        '''
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.verb = verbose
        self.data = None


        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind((self.ip, self.port))
            self.sock.setblocking(0)
            self.sock.settimeout(0.01)
            # This option set buffer size
            # Every self.sock.recv() empty the buffer,
            # so we have always the last incomming value
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
            if self.verb:
                print('Plug : IP = {} Port = {} Buffer Size = {}'.
                      format(ip, port, buffer_size))
        except:
            if self.verb:
                print('No connected on {0}:{1}'.format(self.ip, self.port))

    def listen(self):
        '''Return decoded OSC data in a list, or None.'''
        try:
            raw_data = self.sock.recv(self.buffer_size)
            ##if self.verb:
                ##print("Binary received from {0}:{1} : {2}".format(self.ip,
                                                ##self.port, raw_data))
            self.convert_data(raw_data)
        except:
            if self.verb:
                print('Nothing from {0}:{1}'.format(self.ip, self.port))
        return self.data

    def convert_data(self, raw_data):
        '''Return decoded data in a list, from raw binary data.'''
        try:
            self.data = decodeOSC(raw_data)
            if self.verb:
                print("Decoded OSC message: {0}".format(self.data))
        except:
            if self.verb:
                print('Impossible to decode {0}'.format(raw_data))

class Send():
    '''Create your OSC messge with OSCcodec,
    example:
    msg = OSCMessage("/my/osc/address")
    msg.append('something')
    See OSCcodec documentation in OSCcodec.html.
    '''

    def __init__(self, verbose=True):
        '''Create an UDP socket.'''
        self.verb = verbose
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_to(self, msg, address):
        '''Send msg to address = tuple = (ip:port)
        msg is an OSC message create with OSCMessage()
        address is a tuple.
        '''
        self.sock.sendto(msg.getBinary(), address)

    def simple_send_to(self, title, value, address):
        '''Create and send OSC message:

        tille: string beginning with "/
        value: int, str, list, dict,
                dict are conert to list

        example:
        simple_send_to((127.0.0.1, 8000), "/spam", 1.023)
        '''
        msg = OSCMessage(title, value)
        self.send_to(msg, address)
        if self.verb:
            print("OSC message sended: {0}".format(msg))


if __name__ == "__main__":
    # impossible character
    ##'Œ', œ, 合久必分, 分久必合 :
    from time import sleep

    buffer_size = 1024

    ip_in = "127.0.0.1"
    port_in = 9000

    ip_out = "127.0.0.1"
    port_out = 9000

    my_receiver = Receive(ip_in, port_in, buffer_size, verbose=False)
    my_sender = Send(verbose=False)

    print("\n\nTest bug unicode\n")
    test = ['éé éé']

    msg = OSCMessage("/test")
    msg.append(1)
    msg.append(test)
    msg.append("ça va")
    msg.append("où été")
    msg.append(1.23)

    my_sender.send_to(msg, (ip_out, port_out))
    sleep(0.01)
    res = my_receiver.listen()
    if res:
        print(res)

    #######################################################################
    type_list = [
    1, 1.234587, "Amour", [1, 2.456, "toto"],
    {1:2, 3:4},
    ]
    print("\n\nTest type")
    for test in type_list:
        my_sender.simple_send_to("/test/", test, (ip_out, port_out))
        sleep(0.01)
        res = my_receiver.listen()
        if res:
            print(test, "=", res[2])
##
    #######################################################################
    print("\n\nTest unicode")
    unicode_list = ['é', 'à', 'é', 'ù', 'î','ê','@','ô','ï','ö','Â',
                    '[', '}', '{', ']', '|', '#', '~', '%', '<', '>',
                     'Ä', 'Ö', 'Ü', 'Ô', 'ë', '.', ',', ';', '/', '*', '+', '-',
                     '0123456789',
                     'abcdefghijklmnopqrstuvwxyz',
                     'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                    'mais enfin', 'é è', '@ é è', 'étù', 'oeuvre',
                    "Ô ! léopard semblables,",
                    "N'ont que l'habit pour tous talents!"
                    ]

    for test in unicode_list:
        my_sender.simple_send_to("/test/", test, (ip_out, port_out))
        sleep(0.01)
        res = my_receiver.listen()
        if res:
            print(test, "=", res[2])

    #######################################################################
    print("\n\nTest bug unicode")
    bug_list = ['éé', 'é ù', 'é é', 'à é', 'ù à',
                "je l'ai emporté à la maison !",
                "tu es un enfoiré",
                '''
    sur un arbre perché,
    c'était un péché (et non pas pêcher).
                ''',
                "à la claire fontaine,\nj'ai chanté tout l'été.",
                "\n",
                "j'ai bien un saut de ligne. fin",
                "dispersée, se recomposera »."
                ]

    for test in bug_list:
        my_sender.simple_send_to("/test/", test, (ip_out, port_out))
        sleep(0.01)
        res = my_receiver.listen()
        if res:
            print(test, "=", res[2])
##
    #######################################################################


