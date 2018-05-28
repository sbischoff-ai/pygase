# -*- coding: utf-8 -*-

class TypeClass:
    @classmethod
        def add_type(cls, name: str):
            '''
            Add a new named type to this enum-like class.
            '''
            cls.__setattr__(name, cls._counter)
            cls._counter += 1