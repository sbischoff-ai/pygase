# pygase

PyGaSe, or Python Game Service, is a library (or framework, whichever name you prefer) that provides
a complete set of high-level components for real-time networking for games.

# pygase.utils

Provides several classes and methods that are either used in PyGaSe code or helpful to users of this library.

## Sendable
```python
Sendable(self, /, *args, **kwargs)
```

Mixin for classes that are supposed to be sendable as part of a PyGaSe package.
Sendables can only have basic Python types as attributes.

### to_bytes
```python
Sendable.to_bytes(self)
```

#### Returns
  A small binary representation of the object.

### from_bytes
```python
Sendable.from_bytes(bytepack:bytes)
```

#### Arguments
 - **bytepack** *bytes*: the bytestring to be parsed to a **Sendable**

#### Returns
  A copy of the object that was packed into byte format

## NamedEnum
```python
NamedEnum(self, /, *args, **kwargs)
```

Enum-like class that provides a dynamic mapping from string labels to integer values

### get
```python
NamedEnum.get(name_or_value)
```

#### Arguments
 - **name_or_value** *str/int*: label or value to de- or encode

#### Returns
  Integer value for given string label or vice versa

#### Raises
  - **TypeError** if argument is neither *int* nor *str*

### register
```python
NamedEnum.register(name:str)
```

#### Arguments
 - **name** *str*: string label to register as new enum value

## sqn
```python
sqn(self, /, *args, **kwargs)
```

Subclass of *int* that provides a residue-class-like behaviour of wrapping back to 1 after a maximum value.
Use it to represent sequence numbers with a fixed number of bytes, when you only need a well-defined ordering
within a specific finite scale. 0 represents the state before the sequence has started.

### set_bytesize
```python
sqn.set_bytesize(bytesize:int)
```

Caution: This will reset the bytesize and wrap-over behaviour for all **sqn** instances.

#### Arguments
 - **bytesize** *int*: new size for the *bytes* representation of **sqn**s

### get_max_sequence
```python
sqn.get_max_sequence()
```

#### Returns
  *int*: maximum sequence number, after which **sqn**s wrap back to 1

### to_bytes
```python
sqn.to_bytes(self)
```

#### Returns
  *bytes* representation of the number of exactly the currenly set bytesize

### from_bytes
```python
sqn.from_bytes(b)
```

#### Arguments
 - **b** *bytes*: bytestring to decode

#### Returns
  **sqn** object that was encoded in given bytestring

## LockedRessource
```python
LockedRessource(self, ressource)
```

This class makes an object available via a thread-locking context manager.

Usage example:
```python
myRessource = { 'foo': 'bar' }
myLockedRessource = LockedRessource(myRessource)
with myLockedRessource() as ressource:
    # do stuff without any other threads meddling with the ressource
```

#### Arguments
 - **ressource**: object to be wrapped

## get_available_ip_addresses
```python
get_available_ip_addresses()
```

#### Returns
  A list of all available IP(v4) addresses the server can be bound to.

