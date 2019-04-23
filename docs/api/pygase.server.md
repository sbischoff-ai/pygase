# pygase

PyGaSe, or Python Game Service, is a library (or framework, whichever name you prefer) that provides
a complete set of high-level components for real-time networking for games.

# pygase.server

Provides the **Server** class.

## Server
```python
Server(self, game_state_store:pygase.gamestate.GameStateStore)
```

Part of the PyGaSe backend that handles connections to clients.

#### Arguments
 - **game_state_store** *GameStateStore*: part of the backend that provides the **GameState**

#### Attributes
 - **connections** *dict*: contains each clients address as a key leading to the
   corresponding **ServerConnection** instance
 - **host_client**: address of the host client, if there is any
 - **game_state_store** *GameStateStore*: part of the backend that provides the **GameState**

#### Properties
 - **hostname** *str*: read-only access to the servers hostname
 - **port** *int*: read-only access to the servers port number

### run
```python
Server.run(self, port:int=0, hostname:str='localhost', event_wire=None)
```

Starts the server under specified address. (Can also be called as a coroutine.)

#### Arguments
 - **port** *int*: port number the server will be bound to, default will be an available
   port chosen by the computers network controller
 - **hostname** *str*: hostname or IP address the server will be bound to.
   Defaults to `'localhost'`.
 - **event_wire**: object to which events are to be repeated
   (has to implement a *_push_event* method and is typically a **GameStateMachine**)

### run_in_thread
```python
Server.run_in_thread(self, port:int=0, hostname:str='localhost', event_wire=None, daemon=True)
```

Starts the server under specified address and in a seperate thread.

See **Server.run(port, hostname)**.

#### Returns
*threading.Thread*: the thread the server loop runs in

### shutdown
```python
Server.shutdown(self)
```

Shuts down the server. (can be restarted via **run**)

### dispatch_event
```python
Server.dispatch_event(self, event_type:str, handler_args:list=[], target_client='all', retries:int=0, ack_callback=None, **kwargs)
```

Sends an event to one or all clients.

#### Arguments
 - **event_type** *str*: string that identifies the event and links it to a handler

#### Optional Arguments
 - **handler_args** *list*: list of positional arguments to be passed to the handler function that will be invoked
   by the client
 - **target_client**: either `'all'` for an event broadcast or a clients address
 - **retries** *int*: number of times the event is to be resent, in the case it times out
 - **ack_callback**: function or coroutine to be executed after the event was received,
   will be passed a reference to the client connection
 - **kwargs** *dict*: keyword arguments to be passed to the handler function

### push_event_handler
```python
Server.push_event_handler(self, event_type:str, handler_func)
```

#### Arguments
 - **event_type** *str*: event type to link the handler function to
 - **handler_func**: function or coroutine to be invoked for events of the given type

