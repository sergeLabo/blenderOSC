#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# OSCcodec.py

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
This script is a part of :

SimpleOSC:
    Copyright (c) Daniel Holth & Clinton McChesney.
pyOSC:
    Copyright (c) 2008-2010, Artem Baguinski <artm@v2.nl> et al., Stock,
    V2_Lab, Rotterdam, Netherlands.
Streaming support (OSC over TCP):
    Copyright (c) 2010 Uli Franke <uli.franke@weiss.ch>, Weiss Engineering,
    Uster, Switzerland.

Sources at:
https://gitorious.org/pyosc/devel/source/6aaf78b0c1e89942a9c5b1952266791b7ae16012:


String are latin-1 encoded and decoded.
Use decodeOSC(data) to convert a binary OSC message data to a Python list.
Use OSCMessage() and OSCBundle() to create OSC message.

'''

import math
import struct
import binascii

global FloatTypes
FloatTypes = [float]

global IntTypes
IntTypes = [int]

global NTP_epoch
from calendar import timegm
NTP_epoch = timegm((1900,1,1,0,0,0)) # NTP time started in 1 Jan 1900
del timegm

global NTP_units_per_second
NTP_units_per_second = 0x100000000 # about 232 picoseconds

######
#
# OSCMessage classes
#
######

class OSCMessage(object):
    """ Builds typetagged OSC messages.

    OSCMessage objects are container objects for building OSC-messages.
    On the 'front' end, they behave much like list-objects, and on the 'back'
    end they generate a binary representation of the message, which can be sent
    over a network socket.
    OSC-messages consist of an 'address'-string (not to be confused with a
    (host, port) IP-address!), followed by a string of 'typetags' associated
    with the message's arguments (ie. 'payload'),and finally the arguments
    themselves, encoded in an OSC-specific way.

    On the Python end, OSCMessage are lists of arguments, prepended by the
    message's address.
    The message contents can be manipulated much like a list:
      >>> msg = OSCMessage("/my/osc/address")
      >>> msg.append('something')
      >>> msg.insert(0, 'something else')
      >>> msg[1] = 'entirely'
      >>> msg.extend([1,2,3.])
      >>> msg += [4, 5, 6.]
      >>> del msg[3:6]
      >>> msg.pop(-2)
      5
      >>> print msg
      /my/osc/address ['something else', 'entirely', 1, 6.0]

    OSCMessages can be concatenated with the + operator. In this case, the
    resulting OSCMessage inherits its address from the left-hand operand.
    The right-hand operand's address is ignored.
    To construct an 'OSC-bundle' from multiple OSCMessage, see OSCBundle!

    Additional methods exist for retreiving typetags or manipulating items as
    (typetag, value) tuples.
    """
    def __init__(self, address="", *args):
        """Instantiate a new OSCMessage.
        The OSC-address can be specified with the 'address' argument.
        The rest of the arguments are appended as data.
        """
        self.clear(address)
        if len(args)>0:
            self.append(*args)

    def setAddress(self, address):
        """Set or change the OSC-address
        """
        self.address = address

    def clear(self, address=""):
        """Clear (or set a new) OSC-address and clear any arguments appended
        so far.
        """
        self.address  = address
        self.clearData()

    def clearData(self):
        """Clear any arguments appended so far"""
        self.typetags = ","
        self.message  = b""

    def append(self, argument, typehint=None):
        """Appends data to the message, updating the typetags based on
        the argument's type. If the argument is a blob (counted
        string) pass in 'b' as typehint.
        'argument' may also be a list or tuple, in which case its elements
        will get appended one-by-one, all using the provided typehint
        """

        if isinstance(argument,dict):
            argument = list(argument.items())
        elif isinstance(argument, OSCMessage):
            raise TypeError("Can only append 'OSCMessage' to 'OSCBundle'")

        if hasattr(argument, '__iter__') and not type(argument) in (str,bytes):
            for arg in argument:
                self.append(arg, typehint)

            return

        if typehint == 'b':
            binary = OSCBlob(argument)
            tag = 'b'
        elif typehint == 't':
            binary = OSCTimeTag(argument)
            tag = 't'
        else:
            tag, binary = OSCArgument(argument, typehint)

        self.typetags += tag
        self.message += binary

    def getBinary(self):
        """Returns the binary representation of the message
        """
        binary = OSCString(self.address)
        binary += OSCString(self.typetags)
        binary += self.message

        return binary

    def __repr__(self):
        """Returns a string containing the decode Message
        """
        return str(decodeOSC(self.getBinary()))

    def __str__(self):
        """Returns the Message's address and contents as a string.
        """
        return "%s %s" % (self.address, str(list(self.values())))

    def __len__(self):
        """Returns the number of arguments appended so far.
        """
        return (len(self.typetags) - 1)

    def __eq__(self, other):
        """Return True if two OSCMessages have the same address & content
        """
        if not isinstance(other, self.__class__):
            return False

        return (self.address == other.address) and \
                (self.typetags == other.typetags) and \
                (self.message == other.message)

    def __ne__(self, other):
        """Return (not self.__eq__(other))
        """
        return not self.__eq__(other)

    def __add__(self, values):
        """Returns a copy of self, with the contents of 'values' appended
        (see the 'extend()' method, below)
        """
        msg = self.copy()
        msg.extend(values)
        return msg

    def __iadd__(self, values):
        """Appends the contents of 'values'
        (equivalent to 'extend()', below)
        Returns self
        """
        self.extend(values)
        return self

    def __radd__(self, values):
        """Appends the contents of this OSCMessage to 'values'
        Returns the extended 'values' (list or tuple)
        """
        out = list(values)
        out.extend(list(self.values()))

        if isinstance(values,tuple):
            return tuple(out)

        return out

    def _reencode(self, items):
        """Erase & rebuild the OSCMessage contents from the given
        list of (typehint, value) tuples.
        """
        self.clearData()
        for item in items:
            self.append(item[1], item[0])

    def values(self):
        """Returns a list of the arguments appended so far."""
        return decodeOSC(self.getBinary())[2:]

    def tags(self):
        """Returns a list of typetags of the appended arguments."""
        return list(self.typetags.lstrip(','))

    def items(self):
        """Returns a list of (typetag, value) tuples for
        the arguments appended so far
        """
        out = []
        values = list(self.values())
        typetags = self.tags()
        for i in range(len(values)):
            out.append((typetags[i], values[i]))

        return out

    def __contains__(self, val):
        """Test if the given value appears in the OSCMessage's arguments."""

        return (val in list(self.values()))

    def __getitem__(self, i):
        """Returns the indicated argument (or slice)."""
        return list(self.values())[i]

    def __delitem__(self, i):
        """Removes the indicated argument (or slice)."""
        items = list(self.items())
        del items[i]

        self._reencode(items)

    def _buildItemList(self, values, typehint=None):
        if isinstance(values, OSCMessage):
            items = list(values.items())
        elif isinstance(values,list):
            items = []
            for val in values:
                if isinstance(val,tuple):
                    items.append(val[:2])
                else:
                    items.append((typehint, val))
        elif isinstance(values,tuple):
            items = [values[:2]]
        else:
            items = [(typehint, values)]

        return items

    def __setitem__(self, i, val):
        """Set indicatated argument (or slice) to a new value.
        'val' can be a single int/float/string, or a (typehint, value) tuple.
        Or, if 'i' is a slice, a list of these or another OSCMessage.
        """
        items = list(self.items())

        new_items = self._buildItemList(val)

        if not isinstance(i,slice):
            if len(new_items) != 1:
                raise TypeError("single-item assignment expects a single value\
                or a (typetag, value) tuple")

            new_items = new_items[0]

        # finally...
        items[i] = new_items

        self._reencode(items)

    def setItem(self, i, val, typehint=None):
        """Set indicated argument to a new value (with typehint)."""
        items = list(self.items())

        items[i] = (typehint, val)

        self._reencode(items)

    def copy(self):
        """Returns a deep copy of this OSCMessage."""
        msg = self.__class__(self.address)
        msg.typetags = self.typetags
        msg.message = self.message
        return msg

    def count(self, val):
        """Returns the number of times the given value occurs in the
        OSCMessage's arguments."""
        return list(self.values()).count(val)

    def index(self, val):
        """Returns the index of the first occurence of the given value in the
        OSCMessage's arguments.
        Raises ValueError if val isn't found.
        """
        return list(self.values()).index(val)

    def extend(self, values):
        """Append the contents of 'values' to this OSCMessage.
        'values' can be another OSCMessage,
        or a list/tuple of ints/floats/strings
        """
        items = list(self.items()) + self._buildItemList(values)

        self._reencode(items)

    def insert(self, i, val, typehint = None):
        """Insert given value (with optional typehint) into the OSCMessage
        at the given index.
        """
        items = list(self.items())

        for item in reversed(self._buildItemList(val)):
            items.insert(i, item)

        self._reencode(items)

    def popitem(self, i):
        """Delete the indicated argument from the OSCMessage, and return it
        as a (typetag, value) tuple.
        """
        items = list(self.items())

        item = items.pop(i)

        self._reencode(items)

        return item

    def pop(self, i):
        """Delete the indicated argument from the OSCMessage, and return it.
        """

        return self.popitem(i)[1]

    def reverse(self):
        """Reverses the arguments of the OSCMessage (in place)."""
        items = list(self.items())

        items.reverse()

        self._reencode(items)

    def remove(self, val):
        """Removes the first argument with the given value from the OSCMessage.
        Raises ValueError if val isn't found."""
        items = list(self.items())

        # this is not very efficient...
        i = 0
        for (t, v) in items:
            if (v == val):
                break
            i += 1
        else:
            raise ValueError("'%s' not in OSCMessage" % str(m))
        # but more efficient than first calling self.values().index(val),
        # then calling self.items(),
        # which would in turn call self.values() again...

        del items[i]

        self._reencode(items)

    def __iter__(self):
        """Returns an iterator of the OSCMessage's arguments."""
        return iter(list(self.values()))

    def __reversed__(self):
        """Returns a reverse iterator of the OSCMessage's arguments."""
        return reversed(list(self.values()))

    def itervalues(self):
        """Returns an iterator of the OSCMessage's arguments."""
        return iter(list(self.values()))

    def iteritems(self):
        """Returns an iterator of the OSCMessage's arguments as
        (typetag, value) tuples.
        """
        return iter(list(self.items()))

    def itertags(self):
        """Returns an iterator of the OSCMessage's arguments' typetags."""
        return iter(self.tags())


class OSCBundle(OSCMessage):
    """Builds a 'bundle' of OSC messages.

    OSCBundle objects are container objects for building OSC-bundles of
    OSC-messages.
    An OSC-bundle is a special kind of OSC-message which contains a list of
    OSC-messages. (And yes, OSC-bundles may contain other OSC-bundles...)

    OSCBundle objects behave much the same as OSCMessage objects, with these
    exceptions:
      - if an item or items to be appended or inserted are not OSCMessage
      objects, OSCMessage objectss are created to encapsulate the item(s)
      - an OSC-bundle does not have an address of its own, only the contained
      OSC-messages do. The OSCBundle's 'address' is inherited by any OSCMessage
      the OSCBundle object creates.
      - OSC-bundles have a timetag to tell the receiver when the bundle should
      be processed. The default timetag value (0) means 'immediately'
    """
    def __init__(self, address="", time=0):
        """Instantiate a new OSCBundle.
        The default OSC-address for newly created OSCMessages
        can be specified with the 'address' argument
        The bundle's timetag can be set with the 'time' argument
        """
        super(OSCBundle, self).__init__(address)
        self.timetag = time

    def __str__(self):
        """Returns the Bundle's contents (and timetag, if nonzero) as a string.
        """
        if (self.timetag > 0.):
            out = "#bundle (%s) [" % self.getTimeTagStr()
        else:
            out = "#bundle ["

        if self.__len__():
            for val in list(self.values()):
                out += "%s, " % str(val)
            out = out[:-2]      # strip trailing space and comma

        return out + "]"

    def setTimeTag(self, time):
        """Set or change the OSCBundle's TimeTag
        In 'Python Time', that's floating seconds since the Epoch
        """
        if time >= 0:
            self.timetag = time

    def getTimeTagStr(self):
        """Return the TimeTag as a human-readable string
        """
        fract, secs = math.modf(self.timetag)
        out = time.ctime(secs)[11:19]
        out += ("%.3f" % fract)[1:]

        return out

    def append(self, argument, typehint = None):
        """Appends data to the bundle, creating an OSCMessage to encapsulate
        the provided argument unless this is already an OSCMessage.
        Any newly created OSCMessage inherits the OSCBundle's address at the
        time of creation.
        If 'argument' is an iterable, its elements will be encapsuated by a
        single OSCMessage.
        Finally, 'argument' can be (or contain) a dict, which will be
        'converted' to an OSCMessage;
          - if 'addr' appears in the dict, its value overrides the OSCBundle's
            address
          - if 'args' appears in the dict, its value(s) become the OSCMessage's
            arguments
        """
        if isinstance(argument, OSCMessage):
            binary = OSCBlob(argument.getBinary())
        else:
            msg = OSCMessage(self.address)
            if isinstance(argument,dict):
                if 'addr' in argument:
                    msg.setAddress(argument['addr'])
                if 'args' in argument:
                    msg.append(argument['args'], typehint)
            else:
                msg.append(argument, typehint)

            binary = OSCBlob(msg.getBinary())

        self.message += binary
        self.typetags += 'b'

    def getBinary(self):
        """Returns the binary representation of the message
        """
        binary = OSCString("#bundle")
        binary += OSCTimeTag(self.timetag)
        binary += self.message

        return binary

    def _reencapsulate(self, decoded):
        if decoded[0] == "#bundle":
            msg = OSCBundle()
            msg.setTimeTag(decoded[1])
            for submsg in decoded[2:]:
                msg.append(self._reencapsulate(submsg))

        else:
            msg = OSCMessage(decoded[0])
            tags = decoded[1].lstrip(',')
            for i in range(len(tags)):
                msg.append(decoded[2+i], tags[i])

        return msg

    def values(self):
        """Returns a list of the OSCMessages appended so far."""
        out = []
        for decoded in decodeOSC(self.getBinary())[2:]:
            out.append(self._reencapsulate(decoded))

        return out

    def __eq__(self, other):
        """Return True if two OSCBundles have the same timetag & content."""
        if not isinstance(other, self.__class__):
            return False

        return (self.timetag == other.timetag)\
                and (self.typetags == other.typetags)\
                and (self.message == other.message)

    def copy(self):
        """Returns a deep copy of this OSCBundle."""
        copy = super(OSCBundle, self).copy()
        copy.timetag = self.timetag
        return copy


######
#
# OSCMessage encoding functions
#
######

def OSCString(next):
    """Convert a string into a zero-padded OSC String.
    The length of the resulting string is always a multiple of 4 bytes.
    The string ends with 1 to 4 zero-bytes ('\x00')
    """
    OSCstringLength = math.ceil((len(next)+1) / 4.0) * 4
    return struct.pack(">%ds" % (OSCstringLength), next.encode('latin-1'))

def OSCBlob(next):
    """Convert a string into an OSC Blob.
    An OSC-Blob is a binary encoded block of data,
    prepended by a 'size' (int32).
    The size is always a mutiple of 4 bytes.
    The blob ends with 0 to 3 zero-bytes ('\x00')
    """
    if isinstance(next,str):
        next = next.encode('latin-1')
    if isinstance(next,bytes):
        OSCblobLength = math.ceil((len(next)) / 4.0) * 4
        binary = struct.pack(">i%ds" % (OSCblobLength), OSCblobLength, next)
    else:
        binary = b''

    return binary

def OSCArgument(next, typehint=None):
    """ Convert some Python types to their
    OSC binary representations, returning a
    (typetag, data) tuple.
    """
    if not typehint:
        if type(next) in FloatTypes:
            binary  = struct.pack(">f", float(next))
            tag = 'f'
        elif type(next) in IntTypes:
            binary  = struct.pack(">i", int(next))
            tag = 'i'
        else:
            binary  = OSCString(next)
            tag = 's'

    elif typehint == 'd':
        try:
            binary  = struct.pack(">d", float(next))
            tag = 'd'
        except ValueError:
            binary  = OSCString(next)
            tag = 's'

    elif typehint == 'f':
        try:
            binary  = struct.pack(">f", float(next))
            tag = 'f'
        except ValueError:
            binary  = OSCString(next)
            tag = 's'
    elif typehint == 'i':
        try:
            binary  = struct.pack(">i", int(next))
            tag = 'i'
        except ValueError:
            binary  = OSCString(next)
            tag = 's'
    else:
        binary  = OSCString(next)
        tag = 's'

    return (tag, binary)

def OSCTimeTag(time):
    """Convert a time in floating seconds to its
    OSC binary representation
    """
    if time > 0:
        fract, secs = math.modf(time)
        secs = secs - NTP_epoch
        binary = struct.pack('>LL', int(secs),
                             int(fract * NTP_units_per_second))
    else:
        binary = struct.pack('>LL', 0, 1)

    return binary

######
#
# OSCMessage decoding functions
#
######

def _readString(data):
    """Reads the next (null-terminated) block of data.
    """
    length   = data.find(b'\0')
    nextData = int(math.ceil((length+1) / 4.0) * 4)
    readstring = (data[0:length].decode('latin-1'), data[nextData:])
    return readstring

def _readBlob(data):
    """Reads the next (numbered) block of data
    """

    length   = struct.unpack(">i", data[0:4])[0]
    nextData = int(math.ceil((length) / 4.0) * 4) + 4
    return (data[4:length+4], data[nextData:])

def _readInt(data):
    """Tries to interpret the next 4 bytes of the data
    as a 32-bit integer. """

    if(len(data)<4):
        print("Error: too few bytes for int", data, len(data))
        rest = data
        integer = 0
    else:
        integer = struct.unpack(">i", data[0:4])[0]
        rest    = data[4:]

    return (integer, rest)

def _readLong(data):
    """Tries to interpret the next 8 bytes of the data
    as a 64-bit signed integer.
     """

    high, low = struct.unpack(">ll", data[0:8])
    big = (int(high) << 32) + low
    rest = data[8:]
    return (big, rest)

def _readTimeTag(data):
    """Tries to interpret the next 8 bytes of the data
    as a TimeTag.
     """
    high, low = struct.unpack(">LL", data[0:8])
    if (high == 0) and (low <= 1):
        time = 0.0
    else:
        time = int(NTP_epoch + high) + float(low / NTP_units_per_second)
    rest = data[8:]
    return (time, rest)

def _readFloat(data):
    """Tries to interpret the next 4 bytes of the data
    as a 32-bit float.
    """

    if(len(data)<4):
        print("Error: too few bytes for float", data, len(data))
        rest = data
        float = 0
    else:
        float = struct.unpack(">f", data[0:4])[0]
        rest  = data[4:]

    return (float, rest)

def _readDouble(data):
    """Tries to interpret the next 8 bytes of the data
    as a 64-bit float.
    """

    if(len(data)<8):
        print("Error: too few bytes for double", data, len(data))
        rest = data
        float = 0
    else:
        float = struct.unpack(">d", data[0:8])[0]
        rest  = data[8:]

    return (float, rest)

def decodeOSC(data):
    """Converts a binary OSC message to a Python list.
    """
    table = {"i":_readInt, "f":_readFloat, "s":_readString, "b":_readBlob,
            "d":_readDouble, "t":_readTimeTag}
    decoded = []
    address,  rest = _readString(data)
    if address.startswith(","):
        typetags = address
        address = ""
    else:
        typetags = ""

    if address == "#bundle":
        time, rest = _readTimeTag(rest)
        decoded.append(address)
        decoded.append(time)
        while len(rest)>0:
            length, rest = _readInt(rest)
            decoded.append(decodeOSC(rest[:length]))
            rest = rest[length:]

    elif len(rest)>0:
        if not len(typetags):
            typetags, rest = _readString(rest)
        decoded.append(address)
        decoded.append(typetags)
        if typetags.startswith(","):
            for tag in typetags[1:]:
                value, rest = table[tag](rest)
                decoded.append(value)
        else:
            raise OSCError("OSCMessage's typetag-string lacks the magic ','")

    return decoded


if __name__ == '__main__':
    print("Decode some OSC message and bundle from pure data: \n")
    data = [b'/ping\x00\x00\x00,f\x00\x00@I\x0f\xd0',
            b'/ping\x00\x00\x00,f\x00\x00@I\x0f\xd0',
            b'/ham/egg\x00\x00\x00\x00,si\x00pig\x00\x00\x00\x00\x06',
            b'/a/b/c/d/e\x00\x00,si\x00xxxxx\x00\x00\x00\x00\x00\x00\x02',
            b'/\x00\x00\x00,\x00\x00\x00',
            b'/cheese/cheddar\x00,s\x00\x00brie\x00\x00\x00\x00',
            b'#bundle\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x10/ping\x00\x00\x00,f\x00\x00@I\x0f\xd0\x00\x00\x00\x1c/cheese/cheddar\x00,s\x00\x00brie\x00\x00\x00\x00']

    for d in data:
        dec = decodeOSC(d)
        print(dec)

    print("Create some OSC message and bundle:\n")
    msg = OSCMessage("/my/osc/address")
    msg.append('è')
    ##print(msg)
    ##msg.append('créées') this word exist in french --> bug
    print(msg)
    msg.append('something')
    print(msg)
    msg.insert(0, 'something else')
    print(msg)
    msg[1] = 'entirely'
    print(msg)
    msg.extend([1,2,3.])
    print(msg)
    msg += [4, 5, 6.]
    print(msg)
    del msg[3:6]
    print(msg)
    msg.pop(-2)
    print(msg)
    msg.append('''合久必分, 分久必合L d c s coupés é é''')
    print(msg)
