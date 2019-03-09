# -*- coding: utf-8 -*-

import umsgpack

class Sendable:
    '''
    Mixin for classes that are supposed to be sendable as part of a server request or response.
    Sendables can only have basic Python types as attributes and their constructor needs
    to be callable without passing any arguments.
    '''

    def to_bytes(self):
        '''
        Packs and return a small a binary representation of self.

        '''
        return umsgpack.packb(self.__dict__)

    @classmethod
    def from_bytes(cls, bytepack: bytes):
        '''
        Returns a copy of the object that was packed into byte format.
        '''
        try:
            received_sendable = cls()
            received_sendable.__dict__ = umsgpack.unpackb(bytepack)
            return received_sendable
        except (umsgpack.InsufficientDataException, KeyError, TypeError):
            raise TypeError('Bytes could no be parsed into ' + cls.__name__ + '.')

class NamedEnum:

    _values = []

    @classmethod
    def get(cls, name: str):
        return cls._values.index(name)

    @classmethod
    def register(cls, name:str):
        if name not in cls._values:
            cls._values.append(name)

class sqn(int):

    _bytesize = 2
    _max_sequence = int('1' * (_bytesize * 8), 2)

    @classmethod
    def set_bytesize(cls, bytesize: int):
        cls._bytesize = bytesize
        cls._max_sequence = int('1' * (bytesize * 8), 2)

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
