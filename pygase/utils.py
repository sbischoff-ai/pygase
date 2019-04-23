# -*- coding: utf-8 -*-
'''
Provides several classes and methods that are either used in PyGaSe code or helpful to users of this library.
'''

from threading import Lock
from inspect import signature

import umsgpack
import ifaddr

class Sendable:
    '''
    Mixin for classes that are supposed to be sendable as part of a PyGaSe package.
    Sendables can only have basic Python types as attributes.
    '''

    def to_bytes(self):
        '''
        ### Returns
          A small binary representation of the object.
        '''
        return umsgpack.packb(self.__dict__, force_float_precision='single')

    @classmethod
    def from_bytes(cls, bytepack:bytes):
        '''
        ### Arguments
         - **bytepack** *bytes*: the bytestring to be parsed to a **Sendable**

        ### Returns
          A copy of the object that was packed into byte format
        '''
        try:
            received_sendable = object.__new__(cls)
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
    '''
    Enum-like class that provides a dynamic mapping from string labels to integer values
    '''
    _values = []

    @classmethod
    def get(cls, name_or_value):
        '''
        ### Arguments
         - **name_or_value** *str/int*: label or value to de- or encode
        
        ### Returns
          Integer value for given string label or vice versa
        
        ### Raises
          - **TypeError** if argument is neither *int* nor *str*
        '''
        if isinstance(name_or_value, int):
            return cls._values[name_or_value]
        elif isinstance(name_or_value, str):
            return cls._values.index(name_or_value)
        else:
            raise TypeError
        
    @classmethod
    def register(cls, name: str):
        '''
        ### Arguments
         - **name** *str*: string label to register as new enum value
        '''
        if name not in cls._values:
            cls._values.append(name)

class sqn(int):
    '''
    Subclass of *int* that provides a residue-class-like behaviour of wrapping back to 1 after a maximum value.
    Use it to represent sequence numbers with a fixed number of bytes, when you only need a well-defined ordering
    within a specific finite scale. 0 represents the state before the sequence has started.
    '''
    _bytesize = 2
    _max_sequence = int('1' * (_bytesize * 8), 2)

    @classmethod
    def set_bytesize(cls, bytesize: int):
        '''
        Caution: This will reset the bytesize and wrap-over behaviour for all **sqn** instances.

        ### Arguments
         - **bytesize** *int*: new size for the *bytes* representation of **sqn**s
        '''
        cls._bytesize = bytesize
        cls._max_sequence = int('1' * (bytesize * 8), 2)

    @classmethod
    def get_max_sequence(cls):
        '''
        ### Returns
          *int*: maximum sequence number, after which **sqn**s wrap back to 1
        '''
        return cls(cls._max_sequence)

    def __new__(cls, value, *args, **kwargs):
        if value is None:
            value = 0
        elif value > cls._max_sequence:
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
        '''
        ### Returns
          *bytes* representation of the number of exactly the currenly set bytesize
        '''
        return super().to_bytes(self._bytesize, 'big')

    @classmethod
    def from_bytes(cls, b):
        '''
        ### Arguments
         - **b** *bytes*: bytestring to decode
        
        ### Returns
          **sqn** object that was encoded in given bytestring
        '''
        return cls(super().from_bytes(b, 'big'))

class LockedRessource:
    '''
    This class makes an object available via a thread-locking context manager.

    Usage example:
    ```python
    myRessource = { 'foo': 'bar' }
    myLockedRessource = LockedRessource(myRessource)
    with myLockedRessource() as ressource:
        # do stuff without any other threads meddling with the ressource
    ```

    ### Arguments
     - **ressource**: object to be wrapped
    '''
    def __init__(self, ressource):
        self.lock = Lock()
        self.ressource = ressource

    def __enter__(self):
        self.lock.acquire()
        return self.ressource

    def __exit__(self, type, value, traceback):
        self.lock.release()

def get_available_ip_addresses():
    '''
    ### Returns
      A list of all available IP(v4) addresses the server can be bound to.
    '''
    addresses = []
    for adapter in ifaddr.get_adapters():
        for ip_addr in adapter.ips:
            if ip_addr.is_IPv4 and ip_addr.ip[:3] in {'10.', '172', '192', '127'}:
                # only local IPv4 addresses
                addresses.append(ip_addr.ip)
    return addresses
