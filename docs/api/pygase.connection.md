# pygase

PyGaSe, or Python Game Service, is a library (or framework, whichever name you prefer) that provides
a complete set of high-level components for real-time networking for games.

# pygase.connection

This module contains the low-level network logic of PyGaSe and is not supposed to be required
by any users of this library.

## Package
```python
Package(self, sequence:int, ack:int, ack_bitfield:str, events:list=None)
```

A network package that implements the Pygase protocol and is created, sent, received and resolved by
Pygase **Connections**s.

#### Arguments
 - **sequence** *int*: sequence number of the package on its senders side of the connection
 - **ack** *int*: sequence number of the last received package from the recipients side of the connection
A sequence of `0` means no packages have been sent or received.
After `65535` sequence numbers wrap around to `1`, so they can be stored in 2 bytes.
 - **ack_bitfield** *str*: A 32 character string representing the 32 packages prior to `remote_sequence`,
   with the first character corresponding the packge directly preceding it and so forth.
   `'1'` means the package has been received, `'0'` means it hasn't.

#### Optional Arguments
 - **events** *[Event]*: list of Pygase events that is to be attached to this package and sent via network

#### Class Attributes
 - **timeout** *float*: time in seconds after which a package is considered to be lost, `1.0` by default
 - **max_size** *int*: maximum size in bytes a package may have, `2048` by default

#### Attributes
 - **sequence** *sqn*: packages sequence number
 - **ack** *sqn*: last received remote sequence number
 - **ack_bitfield** *str*: acknowledgement status of 32 preceding remote sequence numbers as boolean bitstring

#### Properties
 - **events**: iterable of **Event** objects contained in the package

### add_event
```python
Package.add_event(self, event:pygase.event.Event)
```

#### Arguments
 - **event** *Event*: a Pygase event that is to be attached to this package

#### Raises
 - **OverflowError**: if the package had previously been converted to a datagram and
   and its size with the added event would exceed **max_size**

### get_bytesize
```python
Package.get_bytesize(self)
```

#### Returns
*int*: size of the package as a datagram in bytes

### to_datagram
```python
Package.to_datagram(self)
```

#### Returns
*bytes*: compact bytestring representing the package, which can be sent via a datagram socket

#### Raises
 - **OverflowError**: if the resulting datagram would exceed **max_size**

### from_datagram
```python
Package.from_datagram(datagram:bytes)
```

#### Arguments
 - **datagram** *bytes*: bytestring data, typically received via a socket

#### Returns
*Package*: the package from which the datagram has been created using `to_datagram()`

#### Raises
 - **ProtocolIDMismatchError**: if the first four bytes don't match the Pygase protocol ID

## ClientPackage
```python
ClientPackage(self, sequence:int, ack:int, ack_bitfield:str, time_order:int, events:list=None)
```

Subclass of **Package** that describes packages sent by **ClientConnection**s.

#### Arguments
 - **time_order** *int/sqn*: the clients last known time order

### to_datagram
```python
ClientPackage.to_datagram(self)
```

#### Returns
*bytes*: compact bytestring representing the package, which can be sent via a datagram socket

#### Raises
 - **OverflowError**: if the resulting datagram would exceed **max_size**

### from_datagram
```python
ClientPackage.from_datagram(datagram)
```

#### Arguments
 - **datagram** *bytes*: bytestring data, typically received via a socket

#### Returns
*Package*: the package from which the datagram has been created using `to_datagram()`

#### Raises
 - **ProtocolIDMismatchError**: if the first four bytes don't match the Pygase protocol ID

## ServerPackage
```python
ServerPackage(self, sequence:int, ack:int, ack_bitfield:str, game_state_update:pygase.gamestate.GameStateUpdate, events:list=None)
```

Subclass of **Package** that describes packages sent by **ServerConnection**s.

#### Arguments
 - **game_state_update** *GameStateUpdate*: the servers most recent minimal update for the client

### to_datagram
```python
ServerPackage.to_datagram(self)
```

#### Returns
*bytes*: compact bytestring representing the package, which can be sent via a datagram socket

#### Raises
 - **OverflowError**: if the resulting datagram would exceed **max_size**

### from_datagram
```python
ServerPackage.from_datagram(datagram)
```

#### Arguments
 - **datagram** *bytes*: bytestring data, typically received via a socket

#### Returns
*Package*: the package from which the datagram has been created using `to_datagram()`

#### Raises
 - **ProtocolIDMismatchError**: if the first four bytes don't match the Pygase protocol ID

## Connection
```python
Connection(self, remote_address:tuple, event_handler, event_wire=None)
```

This class resembles a client-server connection via the Pygase protocol.

#### Arguments
 - **remote_address** *(str, int)*: A tuple `('hostname', port)` *required*
 - **event_handler**: An object that has a callable `handle()` attribute that takes
   an **Event** as argument, for example a **Pygase.event.UniversalEventHandler** instance
 - **event_wire**: object to which events are to be repeated (has to implement a *_push_event* method)

#### Attributes
 - **remote_address** *(str, int)*: A tuple `('hostname', port)`
 - **local_sequence** *int*: sequence number of the last sent package
 - **remote_sequence** *int*: sequence number of the last received package
A sequence of `0` means no packages have been sent or received.
After `65535` sequence numbers wrap around to `1`, so they can be stored in 2 bytes.
 - **ack_bitfield** *str*: A 32 character string representing the 32 packages prior to `remote_sequence`,
    with the first character corresponding the packge directly preceding it and so forth.
    `'1'` means the package has been received, `'0'` means it hasn't.
 - **latency**: the last registered RTT (round trip time)
 - **status** *int*: A **ConnectionStatus** value.
 - **quality** *str*: Either `'good'` or `'bad'`, depending on latency. Is used internally for
    congestion avoidance.

### dispatch_event
```python
Connection.dispatch_event(self, event:pygase.event.Event, ack_callback=None, timeout_callback=None)
```

#### Arguments
 - **event** *Event*: the event to be sent to connection partner

#### Optional Arguments
 - **ack_callback**: function or coroutine to be executed after the event was received
 - **timeout_callback**: function or coroutine to be executed if the event was not received

## ClientConnection
```python
ClientConnection(self, remote_address, event_handler)
```

Subclass of **Connection** that describes the client side of a Pygase connection.

#### Attributes
 - **game_state_context** *LockedRessource*: provides thread-safe access to a *GameState* object

### shutdown
```python
ClientConnection.shutdown(self, shutdown_server:bool=False)
```

Shuts down the client connection. (Can also be called as a coroutine.)

#### Optional Arguments
 - **shutdown_server** *bool*: wether or not the server should be shut down too.
    (Only has an effect if the client has host permissions.)

### loop
```python
ClientConnection.loop(self)
```

The loop that will send and receive packages and handle events. (Can also be called as a coroutine.)

## ServerConnection
```python
ServerConnection(self, remote_address:tuple, event_handler, game_state_store, last_client_time_order:pygase.utils.sqn, event_wire=None)
```

Subclass of **Connection** that describes the server side of a Pygase connection.

#### Attributes
 - **game_state_store** *GameStateStore*: the backends **GameStateStore** that provides the state for this client
 - **last_client_time_order** *sqn*: the clients last known time order

### loop
```python
ServerConnection.loop(hostname:str, port:int, server, event_wire)
```

Coroutine that deals with a **Server**s connections to clients.

#### Arguments
 - **hostname** *str*: the hostname to which to bind the server socket
 - **port** *int*: the port number to which to bind the server socket
 - **server** *Server*: the **Server** for which this loop is run
 - **event_wire**: object to which events are to be repeated
   (has to implement a *_push_event* method and is typically a **GameStateMachine**)

