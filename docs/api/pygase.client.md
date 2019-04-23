# pygase

PyGaSe, or Python Game Service, is a library (or framework, whichever name you prefer) that provides
a complete set of high-level components for real-time networking for games.

# pygase.client

Provides the **Client** class.

## Client
```python
Client(self)
```

#### Attributes
 - **connection** *ClientConnection*: object that contains all networking information

### connect
```python
Client.connect(self, port:int, hostname:str='localhost')
```

Open a connection to a PyGaSe server. (Can be called as a coroutine.)

#### Arguments
 - **port** *int*: port number of the server to which to connect

#### Optional Arguments
 - **hostname** *str*: hostname of the server to which to connect

### connect_in_thread
```python
Client.connect_in_thread(self, port:int, hostname:str='localhost')
```

Open a connection in a seperate thread.

See **Client.connect(port, hostname)**.

#### Returns
*threading.Thread*: the thread the client loop runs in

### disconnect
```python
Client.disconnect(self, shutdown_server:bool=False)
```

Close the client connection. (Can also be called as a coroutine.)

#### Optional Arguments
 - **shutdown_server** *bool*: wether or not the server should be shut down.
    (Only has an effect if the client has host permissions.)

### access_game_state
```python
Client.access_game_state(self)
```

Returns a context manager to access the shared game state in a thread-safe way.

Example:
```python
with client.access_game_state() as game_state:
    do_stuff(game_state)
```

### dispatch_event
```python
Client.dispatch_event(self, event_type:str, handler_args:list=[], retries:int=0, ack_callback=None, **kwargs)
```

Sends an event to the server.

#### Arguments
 - **event_type** *str*: string that identifies the event and links it to a handler

#### Optional Arguments
 - **handler_args** *list*: list of positional arguments to be passed to the handler function that will be invoked
   by the server
 - **retries** *int*: number of times the event is to be resent, in the case it times out
 - **ack_callback**: function or coroutine to be executed after the event was received
 - **kwargs** *dict*: keyword arguments to be passed to the handler function

### push_event_handler
```python
Client.push_event_handler(self, event_type:str, handler_func)
```

#### Arguments
 - **event_type** *str*: event type to link the handler function to
 - **handler_func**: function or coroutine to be invoked for events of the given type

