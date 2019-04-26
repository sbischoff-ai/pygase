# pygase

PyGaSe, or Python Game Service, is a library (or framework, whichever name you prefer) that provides
a complete set of high-level components for real-time networking for games.

# pygase.connection
Provide low-level networking logic.

This module is not supposed to be required by users of this library.


## ProtocolIDMismatchError
```python
ProtocolIDMismatchError(self, /, *args, **kwargs)
```
Bytestring could not be identified as a valid PyGaSe package.
## DuplicateSequenceError
```python
DuplicateSequenceError(self, /, *args, **kwargs)
```
Received a package with a sequence number that was already received before.
## Header
```python
Header(self, sequence:int, ack:int, ack_bitfield:str)
```
Create a PyGaSe package header.

#### Arguments
 - `sequence`: package sequence number
 - `ack`: sequence number of the last received package
 - `ack_bitfield`: A 32 character string representing the 32 sequence numbers prior to the last one received,
    with the first character corresponding the packge directly preceding it and so forth.
    '1' means that package has been received, '0' means it hasn't.

#### Attributes
 - `sequence`
 - `ack`
 - `ack_bitfield`

---
Sequence numbers: A sequence of 0 means no packages have been sent or received.
After 65535 sequence numbers wrap around to 1, so they can be stored in 2 bytes.


### to_bytearray
```python
Header.to_bytearray(self) -> bytearray
```
Return 12 bytes representing the header.
### destructure
```python
Header.destructure(self) -> tuple
```
Return the tuple `(sequence, ack, ack_bitfield)`.
### deconstruct_datagram
```python
Header.deconstruct_datagram(datagram:bytes) -> tuple
```
Return a tuple containing the header and the rest of the datagram.

#### Arguments
 - `datagram`: serialized PyGaSe package to deconstruct

#### Returns
`(header, payload)` with `payload` being a bytestring of the rest of the datagram


## Package
```python
Package(self, header:pygase.connection.Header, events:list=None)
```
Create a UDP package implementing the PyGaSe protocol.

#### Arguments
 - `header`: package header as `Header` object

#### Optional Arguments
 - `events`: list of PyGaSe `Event` objects to attach to this package

#### Class Attributes
 - `timeout`: time in seconds after which a package is considered to be lost, 1.0 by default
 - `max_size`: maximum datagram size in bytes, 2048 by default

#### Attributes
 - `header`

#### Properties
 - `events`: list of `Event` objects contained in the package

---
PyGaSe servers and clients use the subclasses `ServerPackage` and `ClientPackage` respectively.
`Package` would also work on its own (it's not an 'abstract' class), in which case you would have
all features of PyGaSe except for a synchronized game state.



### events
Get a list of the events in the package.

### add_event
```python
Package.add_event(self, event:pygase.event.Event) -> None
```
Add a PyGaSe event to the package.

#### Arguments
 - `event`: the `Event` object to attach to this package

#### Raises
 - `OverflowError` if the package has previously been converted to a datagram and
   and its size with the added event would exceed `max_size`


### get_bytesize
```python
Package.get_bytesize(self) -> int
```
Return the size in bytes the package has as a datagram.
### to_datagram
```python
Package.to_datagram(self) -> bytes
```
Return package compactly serialized to `bytes`.

#### Raises
 - `OverflowError` if the resulting datagram would exceed `max_size`


### from_datagram
```python
Package.from_datagram(datagram:bytes) -> 'Package'
```
Deserialize datagram to `Package`.

#### Arguments
 - `datagram`: bytestring to deserialize, typically received via network

#### Returns
`Package` object

#### Raises
 - `ProtocolIDMismatchError` if the first four bytes don't match the PyGaSe protocol ID


## ClientPackage
```python
ClientPackage(self, header:pygase.connection.Header, time_order:int, events:list=None)
```
Subclass of `Package` for packages sent by PyGaSe clients.

#### Arguments
 - `time_order`: the clients last known time order of the game state

#### Attributes
 - `time_order`


### to_datagram
```python
ClientPackage.to_datagram(self) -> bytes
```
Override `Package.to_datagram` to include `time_order`.
### from_datagram
```python
ClientPackage.from_datagram(datagram:bytes) -> 'ClientPackage'
```
Override `Package.from_datagram` to include `time_order`.
## ServerPackage
```python
ServerPackage(self, header:pygase.connection.Header, game_state_update:pygase.gamestate.GameStateUpdate, events:list=None)
```
Subclass of `Package` for packages sent by PyGaSe servers.

#### Arguments
 - `game_state_update`: the servers most recent minimal update for the client


### to_datagram
```python
ServerPackage.to_datagram(self) -> bytes
```
Override `Package.to_datagram` to include `game_state_update`.
### from_datagram
```python
ServerPackage.from_datagram(datagram:bytes) -> 'ServerPackage'
```
Override `Package.from_datagram` to include `game_state_update`.
## ConnectionStatus
```python
ConnectionStatus(self, /, *args, **kwargs)
```

Enum for the state of a connection:
 - `'Disconnected'`
 - `'Connecting'`
 - `'Connected'`


## Connection
```python
Connection(self, remote_address:tuple, event_handler, event_wire=None)
```
Exchange packages between PyGaSe clients and servers.

PyGaSe connections exchange events with their other side which are handled using custom handler functions.
They also keep each other informed about which packages have been sent and received and automatically avoid
network congestion.

#### Arguments
 - `remote_address`: tuple `('hostname', port)` for the connection partner's address
 - `event_handler`: object that has a callable `handle` attribute that takes
    an `Event` as argument, for example a `PyGaSe.event.UniversalEventHandler` instance
 - `event_wire`: object to which events are to be repeated
    (has to implement a `_push_event` method like `pygase.GameStateMachine`)

#### Attributes
 - `remote_address`
 - `event_handler`
 - `event_wire`
 - `local_sequence`: sequence number of the last sent package
 - `remote_sequence`: sequence number of the last received package
 - `ack_bitfield`: acks for the 32 packages prior to `remote_sequence`
 - `latency`: the last registered RTT (round trip time)
 - `status`: a `ConnectionStatus` value that informs about the state of the connections
 - `quality`: either `'good'` or `'bad'` depending on latency, used internally for
    congestion avoidance

---
PyGaSe servers and clients use the subclasses `ServerConnection` and `ClientConnection` respectively.
`Connection` would also work on its own (it's not an 'abstract' class), in which case you would have
all features of PyGaSe except for a synchronized game state.

### dispatch_event
```python
Connection.dispatch_event(self, event:pygase.event.Event, ack_callback=None, timeout_callback=None)
```
Send an event to the connection partner.

#### Arguments
 - `event`: the event to dispatch

#### Optional Arguments
 - `ack_callback`: function or coroutine to be executed after the event was received
 - `timeout_callback`: function or coroutine to be executed if the event was not received

---
Using long-running blocking operations in any of the callback functions can disturb the connection.


## ClientConnection
```python
ClientConnection(self, remote_address:tuple, event_handler)
```
Subclass of `Connection` to describe the client side of a PyGaSe connection.

Client connections hold a copy of the game state which is continously being updated according to
state updates received from the server.

#### Attributes
 - `game_state_context`: provides thread-safe access to a `GameState` object


### shutdown
```python
ClientConnection.shutdown(self, shutdown_server:bool=False)
```
Shut down the client connection.

This method can also be spawned as a coroutine.

#### Optional Arguments
 - `shutdown_server`: wether or not the server should be shut down too
    (only has an effect if the client has host permissions)


### loop
```python
ClientConnection.loop(self)
```
Continously operate the connection.

This method will keep sending and receiving packages and handling events until it is cancelled or
the connection receives a shutdown command. It can also be spawned as a coroutine.


## ServerConnection
```python
ServerConnection(self, remote_address:tuple, event_handler, game_state_store, last_client_time_order:pygase.utils.Sqn, event_wire=None)
```
Subclass of `Connection` that describes the server side of a PyGaSe connection.

#### Arguments
 - `game_state_store`: object that serves as an interface to the game state repository
    (has to provide the methods `get_gamestate`, `get_update_cache` and `push_update`like `pygase.GameStateStore`)
 - `last_client_time_order`: the last time order number known to the client

#### Attributes
 - `game_state_store`
 - `last_client_time_order`


### loop
```python
ServerConnection.loop(hostname:str, port:int, server, event_wire) -> None
```
Continously orchestrate and operate connections to clients.

This coroutine will keep listening for client packages, create new `ServerConnection` objects
when necessary and make sure all packages are handled by and sent via the right connection.

It will return as soon as the server receives a shutdown message.

#### Arguments
 - `hostname`: the hostname to which to bind the server socket
 - `port`: the port number to which to bind the server socket
 - `server`: the `pygase.Server` for which this loop is run
 - `event_wire`: object to which events are to be repeated
   (has to implement a `_push_event` method and is typically a `pygase.GameStateMachine`)


