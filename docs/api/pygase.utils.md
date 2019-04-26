# pygase

PyGaSe, or Python Game Service, is a library (or framework, whichever name you prefer) that provides
a complete set of high-level components for real-time networking for games.

# pygase.utils
Use helpful classes and functions.

Provides utilities used in PyGaSe code or helpful to users of this library.


## Sendable
```python
Sendable(self, /, *args, **kwargs)
```
Send objects via UDP packages.

This mixin for classes that are supposed to be sendable as part of a PyGaSe package makes
objects serializable with the msgpack protocol.
Sendables can only have attributes of type `str`, `bytes`, `Sqn`, `int`, `float`, `bool`
as well as `list`s or `tuple`s of such.


### to_bytes
```python
Sendable.to_bytes(self) -> bytes
```
Serialize the object to a compact bytestring.
### from_bytes
```python
Sendable.from_bytes(bytepack:bytes)
```
Deserialize a bytestring into an instance of this class.

#### Arguments
 - `bytepack`: the bytestring to be parsed to a subclass of `Sendable`

#### Returns
a copy of an object that was serialized via `Sendable.to_bytes`


## NamedEnum
```python
NamedEnum(self, /, *args, **kwargs)
```
Map string labels to integer values.

This is a base class meant to be subclassed to produce a dynamic enum mapping type.

Example:
```python
class MyEnum(NamedEnum):

    '''Encode labels in integers.
     - "foo"
     - "bar"

    '''


    MyEnum.register("foo")
    MyEnum.register("bar")

    assert MyEnum.get("foo") == 1
    assert MyEnum.get("bar") == 2
    assert MyEnum.get(1) == "foo"
    assert MyEnum.get(2) == "bar"
```


### get
```python
NamedEnum.get(name_or_value)
```
Get the value for a label or vice versa.

#### Arguments
 - `name_or_value`: label or value to de- or encode

#### Returns
int value for given string label or vice versa

#### Raises
  - `TypeError` if argument is neither `int` nor `str`


### register
```python
NamedEnum.register(name:str) -> None
```
Add a new label to the mapping.

#### Arguments
 - `name`: string label to register as new enum value


## Sqn
```python
Sqn(self, /, *args, **kwargs)
```
Use finite periodic integers that fit in 2 bytes.

Subclass of `int` that provides a residue-class-like behaviour of wrapping back to 1 after a maximum value.
Use it to represent sequence numbers with a fixed number of bytes when you only need well-defined ordering
within a specific finite scale. 0 represents the state before the sequence has started.

For the default bytesize of 2 the maximum sequence number is 65535.


### set_bytesize
```python
Sqn.set_bytesize(bytesize:int) -> None
```
Redefine the bytesize and wrap-over behaviour for all `Sqn` instances.

#### Arguments
 - `bytesize`: new size for the `bytes` representation of `Sqn` instances


### get_max_sequence
```python
Sqn.get_max_sequence() -> int
```
Return the maximum sequence number after which `Sqn`s wrap back to 1.
### to_sqn_bytes
```python
Sqn.to_sqn_bytes(self) -> bytes
```
Return representation of the number in exactly the currenly set bytesize.

The default bytesize is 2.


### from_sqn_bytes
```python
Sqn.from_sqn_bytes(bytestring:bytes) -> 'Sqn'
```
Return `Sqn` object that was encoded in given bytestring.
## LockedRessource
```python
LockedRessource(self, ressource)
```
Access a ressource thread-safely.

This class makes an object available via a context manager that essentialy attaches a
`threading.Lock` to it, that threads writing to this object should abide.

Usage example:
```python
myRessource = { 'foo': 'bar' }
myLockedRessource = LockedRessource(myRessource)
with myLockedRessource() as ressource:
    # do stuff without any other threads meddling with the ressource
```

#### Arguments
 - `ressource`: object to be wrapped

### Attributes
 - `lock`: `threading.Lock` that threads writing to `ressource` should abide.
 - `ressource`


## get_available_ip_addresses
```python
get_available_ip_addresses() -> list
```
Return a list of all locally available IPv4 addresses.
