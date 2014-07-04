#!/usr/bin/python3
# -*- coding: UTF-8 -*-

# osc-message.py

#############################################################################
# Original Comments
# from txosc: http://opensoundcontrol.org/implementation/python-txosc
# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.
#############################################################################

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

"""
Open Sound Control 1.1 protocol message generation and parsing

This file is not Twisted-specific. Thoses classes implement OSC message
generation and parsing. Each message has an address and might have some
arguments. Messages can be grouped in bundles.

The protocol is specified in OSC 1.0 specification at
U{http://opensoundcontrol.org/spec-1_0} and has been further extended
in the paper which can be found at U{http://opensoundcontrol.org/spec-1_1}.

-------------------------------------------------------------------------------
Changelog:
-------------------------------------------------------------------------------
3 july 2014
    Migrated to python3 with 2to3


"""
import string
import math
import struct
import re


class OscError(Exception):
    """
    Any error raised by this module.
    """
    pass


def getAddressParts(address):
    """
    Returns the list of the parts of an address.
    @rtype: C{list}
    @return: List of strings.
    @param address: An OSC address
    @type address: C{str}
    """
    return address.strip("/").split("/")


class Message(object):
    """
    An OSC Message element.

    @ivar address: The OSC address string, e.g. C{"/foo/bar"}.
    @type address: C{str}
    @ivar arguments: The L{Argument} instances for the message.
    @type argument: C{list}
    """

    def __init__(self, address, *args):
        self.address = address
        self.arguments = []
        for arg in args:
            self.add(arg)


    def toBinary(self):
        """
        Encodes the L{Message} to binary form, ready to send over the wire.

        @return: A string with the binary presentation of this L{Message}.
        """
        return StringArgument(self.address).toBinary() + StringArgument("," + self.getTypeTags()).toBinary() + "".join([a.toBinary() for a in self.arguments])


    def getTypeTags(self):
        """
        Return the OSC type tags for this message.

        @return: A string with this message's OSC type tag, e.g. C{"ii"} when there are 2 int arguments.
        """
        return "".join([a.typeTag for a in self.arguments])


    def add(self, value):
        """
        Adds an argument to this message with given value, using L{createArgument}.

        @param value: Argument to add to this message. Can be any
        Python type, or an L{Argument} instance.
        """
        if not isinstance(value, Argument):
            value = createArgument(value)
        self.arguments.append(value)


    @staticmethod
    def fromBinary(data):
        """
        Creates a L{Message} object from binary data that is passed to it.

        This static method is a factory for L{Message} objects.
        It checks the type tags of the message, and parses each of its
        arguments, calling each of the proper factory.

        @param data: String of bytes/characters formatted following the OSC protocol.
        @type data: C{str}
        @return: Two-item tuple with L{Message} as the first item, and the
        leftover binary data, as a L{str}.
        """
        osc_address, leftover = _stringFromBinary(data)
        message = Message(osc_address)
        type_tags, leftover = _stringFromBinary(leftover)

        if type_tags[0] != ",":
            # invalid type tag string
            raise OscError("Invalid typetag string: %s" % type_tags)

        for type_tag in type_tags[1:]:
            arg, leftover = _argumentFromBinary(type_tag, leftover)
            message.arguments.append(arg)

        return message, leftover


    def __str__(self):
        s = self.address
        if self.arguments:
            args = " ".join([str(a) for a in self.arguments])
            s += " ,%s %s" % (self.getTypeTags(), args)
        return s

    def getValues(self):
        """
        Returns a list of each argument's value.
        @rtype: C{list}
        """
        return [arg.value for arg in self.arguments]

    def __eq__(self, other):
        if self.address != other.address:
            return False
        if len(self.arguments) != len(other.arguments):
            return False
        if self.getTypeTags() != other.getTypeTags():
            return False
        for i in range(len(self.arguments)):
            if self.arguments[i].value != other.arguments[i].value:
                return False
        return True

    def __ne__(self, other):
        return not (self == other)


class Bundle(object):
    """
    An OSC Bundle element.

    @ivar timeTag: A L{TimeTagArgument}, representing the time for this bundle.
    @ivar elements: A C{list} of OSC elements (L{Message} or L{Bundle}s).
    """
    timeTag = None
    elements = None

    def __init__(self, elements=None,  timeTag=True):
        if elements:
            self.elements = elements
        else:
            self.elements = []

        self.timeTag = timeTag


    def toBinary(self):
        """
        Encodes the L{Bundle} to binary form, ready to send over the wire.

        @return: A string with the binary presentation of this L{Bundle}.
        """
        data = StringArgument("#bundle").toBinary()
        data += TimeTagArgument(self.timeTag).toBinary()
        for msg in self.elements:
            binary = msg.toBinary()
            data += IntArgument(len(binary)).toBinary()
            data += binary
        return data


    def add(self, element):
        """
        Add an element to this bundle.

        @param element: A L{Message} or a L{Bundle}.
        """
        self.elements.append(element)


    def __eq__(self, other):
        if len(self.elements) != len(other.elements):
            return False
        for i in range(len(self.elements)):
            if self.elements[i] != other.elements[i]:
                return False
        return True


    def __ne__(self, other):
        return not (self == other)


    @staticmethod
    def fromBinary(data):
        """
        Creates a L{Bundle} object from binary data that is passed to it.

        This static method is a factory for L{Bundle} objects.

        @param data: String of bytes formatted following the OSC protocol.
        @return: Two-item tuple with L{Bundle} as the first item, and the
        leftover binary data, as a L{str}. That leftover should be an empty string.
        """
        bundleStart, data = _stringFromBinary(data)
        if bundleStart != "#bundle":
            raise OscError("Error parsing bundle string")
        bundle = Bundle()
        bundle.timeTag, data = TimeTagArgument.fromBinary(data)
        while data:
            size, data = IntArgument.fromBinary(data)
            size = size.value
            if len(data) < size:
                raise OscError("Unexpected end of bundle: need %d bytes of data" % size)
            payload = data[:size]
            bundle.elements.append(_elementFromBinary(payload))
            data = data[size:]
        return bundle, ""


    def getMessages(self):
        """
        Retrieve all L{Message} elements from this bundle, recursively.

        @return: L{set} of L{Message} instances.
        """
        r = set()
        for m in self.elements:
            if isinstance(m, Bundle):
                r = r.union(m.getMessages())
            else:
                r.add(m)
        return r


class Argument(object):
    """
    Base OSC argument class.

    @ivar typeTag: A 1-character C{str} which represents the OSC type
        of this argument. Every subclass must define its own typeTag.
    """
    typeTag = None

    def __init__(self, value):
        self.value = value
        self._check_type()

    def _check_type(self):
        """
        Does the type checking for the value.
        """
        pass


    def toBinary(self):
        """
        Encodes the L{Argument} to binary form, ready to send over the wire.

        @return: A string with the binary presentation of this L{Message}.
        """
        raise NotImplementedError('Override this method')


    @staticmethod
    def fromBinary(data):
        """
        Creates a L{Message} object from binary data that is passed to it.

        This static method is a factory for L{Argument} objects.
        Each subclass of the L{Argument} class implements it to create an
        instance of its own type, parsing the data given as an argument.

        @param data: C{str} of bytes formatted following the OSC protocol.
        @return: Two-item tuple with L{Argument} as the first item, and the
        leftover binary data, as a L{str}.
        """
        raise NotImplementedError('Override this method')


    def __str__(self):
        return "%s:%s " % (self.typeTag, self.value)


#
# OSC 1.1 required arguments
#

class BlobArgument(Argument):
    """
    An L{Argument} representing arbitrary binary data.
    """
    typeTag = "b"

    def toBinary(self):
        """
        See L{Argument.toBinary}.
        """
        sz = len(self.value)
        #length = math.ceil((sz+1) / 4.0) * 4
        length = _ceilToMultipleOfFour(sz)
        return struct.pack(">i%ds" % (length), sz, str(self.value))


    @staticmethod
    def fromBinary(data):
        """
        See L{Argument.fromBinary}.
        """
        try:
            length = struct.unpack(">i", data[0:4])[0]
            index_of_leftover = _ceilToMultipleOfFour(length) + 4
            if len(data)+4 < length:
                raise OscError("Not enough bytes to find size of a blob of size %s in %s." % (length, data))
            blob_data = data[4:length + 4]
        except struct.error:
            raise OscError("Not enough bytes to find size of a blob argument in %s." % (data))
        leftover = data[index_of_leftover:]
        return BlobArgument(blob_data), leftover



class StringArgument(Argument):
    """
    An argument representing a C{str}.
    """

    typeTag = "s"

    def toBinary(self):
        length = math.ceil((len(self.value)+1) / 4.0) * 4
        return struct.pack(">%ds" % (length), str(self.value))


    @staticmethod
    def fromBinary(data):
        """
        Creates a L{StringArgument} object from binary data that is passed to it.

        This static method is a factory for L{StringArgument} objects.

        OSC-string A sequence of non-null ASCII characters followed by a null,
        followed by 0-3 additional null characters to make the total number
        of bits a multiple of 32.

        @param data: String of bytes/characters formatted following the OSC protocol.
        @return: Two-item tuple with L{StringArgument} as the first item, and the leftover binary data, as a L{str}.

        """
        value, leftover = _stringFromBinary(data)
        return StringArgument(value), leftover



class IntArgument(Argument):
    """
    An L{Argument} representing a 32-bit signed integer.
    """
    typeTag = "i"

    def _check_type(self):
        if type(self.value) not in [int, int]:
            raise TypeError("Value %s must be an integer or a long, not a %s." % (self.value, type(self.value).__name__))

    def toBinary(self):
        if self.value >= 1<<31:
            raise OverflowError("Integer too large: %d" % self.value)
        if self.value < -1<<31:
            raise OverflowError("Integer too small: %d" % self.value)
        return struct.pack(">i", int(self.value))


    @staticmethod
    def fromBinary(data):
        try:
            i = struct.unpack(">i", data[:4])[0]
            leftover = data[4:]
        except struct.error:
            raise OscError("Too few bytes left to get an int from %s." % (data))
            #FIXME: do not raise error and return leftover anyways ?
        return IntArgument(i), leftover

    def __int__(self):
        return int(self.value)

class FloatArgument(Argument):
    """
    An L{Argument} representing a 32-bit floating-point value.
    """

    typeTag = "f"

    def _check_type(self):
        if type(self.value) not in [float, int, int]:
            raise TypeError("Value %s must be a float, an int or a long, not a %s." % (self.value, type(self.value).__name__))

    def toBinary(self):
        return struct.pack(">f", float(self.value))

    @staticmethod
    def fromBinary(data):
        try:
            f = struct.unpack(">f", data[:4])[0]
            leftover = data[4:]
        except struct.error:
            raise OscError("Too few bytes left to get a float from %s." % (data))
            #FIXME: do not raise error and return leftover anyways ?
        return FloatArgument(f), leftover

    def __float__(self):
        return float(self.value)

class TimeTagArgument(Argument):
    """
    An L{Argument} representing an OSC time tag.

    Like NTP timestamps, the binary representation of a time tag is a
    64 bit fixed point number. The first 32 bits specify the number of
    seconds since midnight on January 1, 1900, and the last 32 bits
    specify fractional parts of a second to a precision of about 200
    picoseconds.

    The time tag value consisting of 63 zero bits followed by a one in
    the least signifigant bit is a special case meaning "immediately."

    In the L{TimeTagArgument} class, the timetag value is a float, or
    'True' when 'Immediately' is meant.

    """
    typeTag = "t"

    def __init__(self, value=True):
        Argument.__init__(self, value)


    def toBinary(self):
        if self.value is True:
            return struct.pack('>ll', 0, 1)
        fr, sec = math.modf(self.value)
        return struct.pack('>ll', int(sec), int(fr * 1e9))


    @staticmethod
    def fromBinary(data):
        binary = data[0:8]
        if len(binary) != 8:
            raise OscError("Too few bytes left to get a timetag from %s." % (data))
        leftover = data[8:]

        if binary == '\0\0\0\0\0\0\0\1':
            # immediately
            time = True
        else:
            high, low = struct.unpack(">ll", data[0:8])
            time = float(int(high) + low / float(1e9))
        return TimeTagArgument(time), leftover



class BooleanArgument(Argument):
    """
    An L{Argument} representing C{True} or C{False}.
    """

    def __init__(self, value):
        Argument.__init__(self, value)
        if self.value:
            self.typeTag = "T"
        else:
            self.typeTag = "F"

    def toBinary(self):
        return "" # bool args do not have data, just a type tag

    def __bool__(self):
        return bool(self.value)

class _DatalessArgument(Argument):
    """
    Abstract L{Argument} class for defining arguments whose value is
    defined just by its type tag.

    This class should not be used directly. It is intended to gather
    common behaviour of L{NullArgument} and L{ImpulseArgument}.
    """

    def __init__(self, ignoreValue=None):
        Argument.__init__(self, self.value)


    def toBinary(self):
        return ""



class NullArgument(_DatalessArgument):
    """
    An L{Argument} representing C{None}.
    """
    typeTag = "N"
    value = None



class ImpulseArgument(_DatalessArgument):
    """
    An L{Argument} representing the C{"bang"} impulse.
    """
    typeTag = "I"
    value = True


#
# Optional arguments
#
# Should we implement all types that are listed "optional" in
# http://opensoundcontrol.org/spec-1_0 ?

class _FourByteArgument(Argument):
    """
    An abstract 32-bit L{Argument} whose data is a tuple of four integers in the range [0,255].
    """
    def __init__(self, value=(0, 0, 0, 0)):
        """
        @param value: A tuple of four integers in the range [0,255].
        @type value: C{tuple}
        """
        Argument.__init__(self, value)

    def _check_type(self):
        if type(self.value) not in [list, tuple]:
            raise TypeError("Value %s must be a list of integers, not a %s." % (self.value, type(self.value).__name__))
        if len(self.value) != 4:
            raise TypeError("Value %s must contain 4 elements." % (self.value))
        for element in self.value:
            if type(element) not in [int, int]:
                raise TypeError("Element value %s must be an int, not a %s." % (element, type(element).__name__))
            if element > 255 or element < 0:
                raise TypeError("Element value %s must be between 0 and 255." % (element))


    def toBinary(self):
        """
        See L{Argument.toBinary}.
        """
        # self.value must be a list of 4 int in range [0, 255]
        return struct.pack(">4B", *self.value)


    @staticmethod
    def fromBinary(data):
        """
        See L{Argument.fromBinary}.
        """
        binary = data[0:4]
        if len(binary) != 4:
            raise OscError("Too few bytes left to get four from %s." % (data))
        leftover = data[4:]
        try:
            values = struct.unpack(">4B", binary)
        except struct.error:
            raise OscError("Error trying to find four bytes of data in %s." % (binary))
        return _FourByteArgument(values), leftover




class ColorArgument(_FourByteArgument):
    """
    An L{Argument} representing a 32-bit RGBA color.

    Color arguments are represented as a four-int tuple in the range [0,255]. Each of the color channels are in this order: red, green, blue, alpha.
    """
    typeTag = "r"

    @staticmethod
    def fromBinary(data):
        tmp, leftover = _FourByteArgument.fromBinary(data)
        return ColorArgument(tmp.value), leftover


class MidiArgument(_FourByteArgument):
    """
    An L{Argument} representing a 32-bit MIDI message.

    MIDI "message" arguments contain 4 bytes and is represented as a four-int tuple. Bytes from most significant (left) to least significant (right) are: port id, status byte, data1, data2.
    """
    typeTag = "m"

    @staticmethod
    def fromBinary(data):
        tmp, leftover = _FourByteArgument.fromBinary(data)
        return MidiArgument(tmp.value), leftover

#class SymbolArgument(StringArgument):
#    typeTag = "S"


#global dicts
_types = {
    float: FloatArgument,
    str: StringArgument,
    int: IntArgument,
    bool: BooleanArgument,
    type(None): NullArgument,
    }

_tags = {
    "b": BlobArgument,
    "f": FloatArgument,
    "i": IntArgument,
    "s": StringArgument,
    "t": TimeTagArgument,
    }


def createArgument(value, type_tag=None):
    """
    Creates an OSC argument, trying to guess its type if no type is given.

    Factory of *Attribute objects.
    @param value: Any Python base type.
    @param type_tag: One-letter string. One of C{"sifbTFNI"}.
    @type type_tag: One-letter string.
    @return: Returns an instance of one of the subclasses of the L{Argument} class.
    @rtype: L{Argument} subclass.
    """
    global _types
    global _tags
    kind = type(value)

    if type_tag:
        # Get the argument type based on given type tag
        if type_tag == "T":
            return BooleanArgument(True)
        if type_tag == "F":
            return BooleanArgument(False)
        if type_tag == "N":
            return NullArgument()
        if type_tag == "I":
            return ImpulseArgument()

        if type_tag in list(_tags.keys()):
            return _tags[type_tag](value)

        raise OscError("Unknown type tag: %s" % type)

    else:
        # Guess the argument type based on the type of the value
        if kind in list(_types.keys()):
            return _types[kind](value)

        raise OscError("No OSC argument type for %s (value = %s)" % (kind, value))


#
# private functions
#

def _ceilToMultipleOfFour(num):
    """
    Rounds a number to the closest higher number that is a mulitple of four.
    That is for data that need to be padded with zeros so that the length of their data
    must be a multiple of 32 bits.
    """
    return num + (4 - (num % 4))


def _argumentFromBinary(type_tag, data):
    if type_tag == "T":
        return BooleanArgument(True), data
    if type_tag == "F":
        return BooleanArgument(False), data
    if type_tag == "N":
        return NullArgument(), data
    if type_tag == "I":
        return ImpulseArgument(), data

    global _tags
    if type_tag not in _tags:
        raise OscError("Invalid typetag: %s" % type_tag)

    return _tags[type_tag].fromBinary(data)


def _stringFromBinary(data):
    null_pos = string.find(data, "\0") # find the first null char
    value = data[0:null_pos] # get the first string out of data
    # find the position of the beginning of the next data
    leftover = data[_ceilToMultipleOfFour(null_pos):]
    return value, leftover


def _elementFromBinary(data):
    if data[0] == "/":
        element, data = Message.fromBinary(data)
    elif data[0] == "#":
        element, data = Bundle.fromBinary(data)
    else:
        raise OscError("Error parsing OSC data: " + data)
    return element
