# pygase

PyGaSe, or Python Game Service, is a library (or framework, whichever name you prefer) that provides
a complete set of high-level components for real-time networking for games.

# pygase.event
Handle events in PyGaSe clients, servers and state machines.

Contains the basic components of the PyGaSe event framework.


## Event
```python
Event(self, event_type:str, *args, **kwargs)
```
Send PyGaSe events and attached data via UDP packages.

#### Arguments
 - `event_type`: string that identifies the event and links it to a handler

#### Optional Arguments
Additional positional arguments represent event data and will be passed to the handler function
on the other side of the connection.

#### Keyword Arguments
keyword arguments to be passed to the handler function on the other side of the connection

#### Attributes
 - `type`
 - `handler_args`
 - `handler_kwargs`


## UniversalEventHandler
```python
UniversalEventHandler(self)
```
Handle PyGaSe events with callback functions.
### register_event_handler
```python
UniversalEventHandler.register_event_handler(self, event_type:str, event_handler_function) -> None
```
Register an event handler for a specific event type.

#### Arguments
 - `event_type`: string that identifies the events to be handled by this function
 - `event_handler_function`: callback function or coroutine that will be invoked with the handler args
   and kwargs with which the incoming event has been dispatched


### handle
```python
UniversalEventHandler.handle(self, event:pygase.event.Event, **kwargs)
```
Invoke the appropriate handler function.

#### Arguments
 - `event`: the event to be handled

#### Keyword Arguments
keyword arguments to be passed to the handler function (in addition to those already attached to the event)


### has_event_type
```python
UniversalEventHandler.has_event_type(self, event_type:str) -> bool
```
Check if a handler was registered for `event_type`.
