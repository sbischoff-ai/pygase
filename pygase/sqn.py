# -*- coding: utf-8 -*-

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
        return super(cls, cls).__new__(cls, value)
    
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
