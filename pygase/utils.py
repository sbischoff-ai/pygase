# -*- coding: utf-8 -*-

from inspect import signature

import umsgpack
import ifaddr

class Sendable:
    '''
    Mixin for classes that are supposed to be sendable as part of a Pygase package.
    Sendables can only have basic Python types as attributes.
    '''

    def to_bytes(self):
        '''
        Packs and returns a small a binary representation of self.
        '''
        return umsgpack.packb(self.__dict__, force_float_precision='single')

    @classmethod
    def from_bytes(cls, bytepack: bytes):
        '''
        Returns a copy of the object that was packed into byte format.
        '''
        try:
            arg_num = len(signature(cls).parameters)
            received_sendable = cls(*([None]*arg_num))
            received_sendable.__dict__ = umsgpack.unpackb(bytepack)
            return received_sendable
        except (umsgpack.InsufficientDataException, KeyError, TypeError):
            raise TypeError('Bytes could no be parsed into ' + cls.__name__ + '.')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

class NamedEnum:

    _values = []

    @classmethod
    def get(cls, name_or_value):
        if isinstance(name_or_value, int):
            return cls._values[name_or_value]
        elif isinstance(name_or_value, str):
            return cls._values.index(name_or_value)
        else:
            raise TypeError
        
    @classmethod
    def register(cls, name: str):
        if name not in cls._values:
            cls._values.append(name)

class sqn(int):

    _bytesize = 2
    _max_sequence = int('1' * (_bytesize * 8), 2)

    @classmethod
    def set_bytesize(cls, bytesize: int):
        cls._bytesize = bytesize
        cls._max_sequence = int('1' * (bytesize * 8), 2)

    @classmethod
    def get_max_sequence(cls):
        return cls(cls._max_sequence)

    def __new__(cls, value, *args, **kwargs):
        if value > cls._max_sequence:
            raise ValueError('value exceeds maximum sequence number')
        elif value < 0:
            raise ValueError('sequence numbers must not be negative')
        return super(sqn, cls).__new__(cls, value)
    
    def __add__(self, other):
        result = super().__add__(other)
        if result > self._max_sequence:
            result -= self._max_sequence
        return self.__class__(result)

    def __sub__(self, other):
        result = super().__sub__(other)
        threshold = (self._max_sequence - 1)/2
        if result > threshold:
            result -= self._max_sequence
        elif result < -threshold:
            result += self._max_sequence
        return int(result)
    
    def __lt__(self, other):
        return super().__lt__(super().__add__((other - self)))

    def __gt__(self, other):
        return super().__gt__(super().__add__((other - self)))

    def to_bytes(self):
        return super().to_bytes(self._bytesize, 'big')

    @classmethod
    def from_bytes(cls, b):
        return cls(super().from_bytes(b, 'big'))

def get_available_ip_addresses():
    """
    Returns a list of all available IP addresses the server can be bound to.
    Keep in mind that `127.0.0.1` is only suitable for local games.
    """
    addresses = []
    for adapter in ifaddr.get_adapters():
        for ip_addr in adapter.ips:
            if ip_addr.is_IPv4 and ip_addr.ip[:3] in {"10.", "172", "192", "127"}:
                # only local IPv4 addresses
                addresses.append(ip_addr.ip)
    return addresses
