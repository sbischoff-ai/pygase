# pygase

PyGaSe, or Python Game Service, is a library (or framework, whichever name you prefer) that provides
a complete set of high-level components for real-time networking for games.

# pygase.server
Serve PyGaSe clients.

Provides the `Server` class.


## Server
```python
Server(self, game_state_store:pygase.gamestate.GameStateStore)
```
Listen to clients and orchestrate the flow of events and state updates.

The `Server` instance does not contain game logic or state, it is only responsible for connections
to clients. The state is provided by a `pygase.GameStateStore` and game logic by a `pygase.GameStateMachine`.

#### Arguments
 - `game_state_store`: part of the backend that provides an interface to the `GameState`

#### Attributes
 - `connections`: contains each clients address as a key leading to the corresponding `ServerConnection` instance
 - `host_client`: address of the host client (who has permission to shutdown the server), if there is any
 - `game_state_store`

#### Properties
 - `hostname`: read-only access to the servers hostname
 - `port`: read-only access to the servers port number


### hostname
Get the hostname or IP address on which the server listens.

Returns `None` when the server is not running.


### port
Get the port number on which the server listens.

Returns `None` when the server is not running.


### run
```python
Server.run(self, port:int=0, hostname:str='localhost', event_wire=None) -> None
```
Start the server under a specified address.

This is a blocking function but can also be spawned as a coroutine or in a thread via `run_in_thread`.

#### Arguments
 - `port`: port number the server will be bound to, default will be an available
   port chosen by the computers network controller
 - `hostname`: hostname or IP address the server will be bound to.
   Defaults to `'localhost'`.
 - `event_wire`: object to which events are to be repeated
   (has to implement a `_push_event(event)` method and is typically a `GameStateMachine`)


### run_in_thread
```python
Server.run_in_thread(self, port:int=0, hostname:str='localhost', event_wire=None, daemon=True) -> threading.Thread
```
Start the server in a seperate thread.

See `Server.run(port, hostname)`.

#### Returns
the thread the server loop runs in


### shutdown
```python
Server.shutdown(self) -> None
```
Shut down the server.

The server can be restarted via `run` in which case it will remember previous connections.
This method can also be spawned as a coroutine.


### dispatch_event
```python
Server.dispatch_event(self, event_type:str, *args, target_client='all', retries:int=0, ack_callback=None, **kwargs) -> None
```
Send an event to one or all clients.

#### Arguments
 - `event_type`: string that identifies the event and links it to a handler

#### Optional Arguments
Additional positional arguments represent event data and will be passed to the clients handler function.

### Keyword Arguments
 - `target_client`: either `'all'` for an event broadcast, or a clients address as a tuple
 - `retries`: number of times the event is to be resent in case it times out
 - `ack_callback`: function or coroutine to be executed after the event was received,
    will be passed a reference to the corresponding `ServerConnection` instance
Additional keyword arguments will be sent as event data and passed to the clients handler function.


### register_event_handler
```python
Server.register_event_handler(self, event_type:str, event_handler_function) -> None
```
Register an event handler for a specific event type.

#### Arguments
 - `event_type`: event type to link the handler function to
 - `handler_func`: function or coroutine to be invoked for events of the given type


