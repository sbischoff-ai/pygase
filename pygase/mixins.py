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
