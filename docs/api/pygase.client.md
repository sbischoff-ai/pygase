# pygase

PyGaSe, or Python Game Service, is a library (or framework, whichever name you prefer) that provides
a complete set of high-level components for real-time networking for games.

# pygase.client
Connect to PyGaSe servers.

Provides the `Client` class.


## Client
```python
Client(self)
```
Exchange events with a PyGaSe server and access a synchronized game state.

#### Attributes
 - `connection`: `ClientConnection` object that contains all networking information


### connect
```python
Client.connect(self, port:int, hostname:str='localhost') -> None
```
Open a connection to a PyGaSe server.

This is a blocking function but can also be spawned as a coroutine or in a thread via `connect_in_thread`.

#### Arguments
 - `port`: port number of the server to which to connect

#### Optional Arguments
 - `hostname`: hostname of the server to which to connect


### connect_in_thread
```python
Client.connect_in_thread(self, port:int, hostname:str='localhost') -> threading.Thread
```
Open a connection in a seperate thread.

See `Client.connect(port, hostname)`.

#### Returns
the thread the client loop runs in


### disconnect
```python
Client.disconnect(self, shutdown_server:bool=False) -> None
```
Close the client connection.

This method can also be spawned as a coroutine.

#### Optional Arguments
 - `shutdown_server`: wether or not the server should be shut down
    (only has an effect if the client has host permissions)


### access_game_state
```python
Client.access_game_state(self)
```
Return a context manager to access the shared game state.

Can be used in a `with` block to lock the synchronized game_state while working with it.

Example:
```python
with client.access_game_state() as game_state:
    do_stuff(game_state)
```


### dispatch_event
```python
Client.dispatch_event(self, event_type:str, *args, retries:int=0, ack_callback=None, **kwargs) -> None
```
Send an event to the server.

#### Arguments
 - `event_type`: event type identifier that links to a handler

#### Optional Arguments
Additional positional arguments represent event data and will be passed to the servers handler function.

#### Keyword Arguments
 - `retries`: number of times the event is to be resent in case it times out
 - `ack_callback`: function or coroutine to be executed after the event was received
Additional keyword arguments will be sent as event data and passed to the handler function.


### register_event_handler
```python
Client.register_event_handler(self, event_type:str, event_handler_function) -> None
```
Register an event handler for a specific event type.

#### Arguments
 - `event_type`: event type to link the handler function to
 - `handler_func`: function or coroutine to be invoked for events of the given type


