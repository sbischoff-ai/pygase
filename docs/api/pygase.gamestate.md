# pygase

PyGaSe, or Python Game Service, is a library (or framework, whichever name you prefer) that provides
a complete set of high-level components for real-time networking for games.

# pygase.gamestate

Provides all PyGaSe components that deal with game states and state progression.

## GameStatus
```python
GameStatus(self, /, *args, **kwargs)
```

Enum for the game simulation status:
 - `'Paused'`
 - `'Active'`


## GameState
```python
GameState(self, time_order:int=0, game_status:int=0, **kwargs)
```
Customize a serializable game state model.

Contains game state information that will be synchronized between the server and the clients.
Via `pygase.utils.Sendable` its instances will be serialized using the msgpack protocol
and must only contain attributes of type `str`, `bytes`, `Sqn`, `int`, `float`, `bool`
as well as `list`s or `tuple`s of such.

#### Optional Arguments
 - `time_order`: current time order number of the game state, higher means more recent
 - `game_status`: `GameStatus` enum value that describes whether or not the game loop is running

#### Keyword Arguments
Provide custom game state attributes via keyword arguments or assign them later.

#### Attributes
  - `game_status`
  - `time_order`
`GameState` instances mainly consist of custom attributes that make up the game state.


### is_paused
```python
GameState.is_paused(self) -> bool
```
Return `True` if game is paused.
## GameStateUpdate
```python
GameStateUpdate(self, time_order:int, **kwargs)
```
Update a `GameState` object.

Contains a set of changes to carry out on a `GameState`.
The server keeps a `time_order` counter and labels all updates in ascending order.

Attributes of a `GameStateUpdate` object represent new values of `GameState` attributes.
To remove game state attributes just assign `TO_DELETE` to it in the update.

Use the `+` operator to add updates to one another and combine them or to add them to a
game state in order to update it.

#### Arguments
 - `time_order`: the time order up to which the update reaches

#### Keyword Arguments
game state attributes to be updated

#### Attributes
 - `time_order`
`GameStateUpdate` instances mainly consist of custom game state attributes to update.


### from_bytes
```python
GameStateUpdate.from_bytes(bytepack:bytes) -> 'GameStateUpdate'
```
Extend `Sendable.from_bytes` to make sure time_order is of type `Sqn`.
## GameStateStore
```python
GameStateStore(self, initial_game_state:pygase.gamestate.GameState=<pygase.gamestate.GameState object at 0x00000215ABA52F28>)
```
Provide access to a game state and manage state updates.

#### Optional Arguments
 - `inital_game_state`: state of the game before the simulation begins


### get_update_cache
```python
GameStateStore.get_update_cache(self) -> list
```
Return the latest state updates.
### get_game_state
```python
GameStateStore.get_game_state(self) -> pygase.gamestate.GameState
```
Return the current game state.
### push_update
```python
GameStateStore.push_update(self, update:pygase.gamestate.GameStateUpdate) -> None
```
Push a new state update to the update cache.

This method will usually be called by whatever is progressing the game state, usually a
`GameStateMachine`.


## GameStateMachine
```python
GameStateMachine(self, game_state_store:pygase.gamestate.GameStateStore)
```
Run a simulation that propagates the game state.

A `GameStateMachine` progresses a game state through time, applying all game simulation logic.
This class is meant either as a base class from which you inherit and implement the `time_step` method,
or you assign a `time_step` implementation after instantiation.

#### Arguments
 - `game_state_store`: part of the PyGaSe backend that provides the state

#### Attributes
 - `game_time`: duration the game has been running in seconds


### register_event_handler
```python
GameStateMachine.register_event_handler(self, event_type:str, event_handler_function) -> None
```
Register an event handler for a specific event type.

For event handlers to have any effect, the events have to be wired from a `Server` to the
`GameStateMachine` via the `event_wire` argument of the servers `run` method.

#### Arguments
 - `event_type`: which type of event to link the handler function to
 - `handler_func`: function or coroutine to be invoked for events of the given type,
    gets passed the keyword argument `game_state` (along with those attached
    to the event) and is expected to return an update dict


### run_game_loop
```python
GameStateMachine.run_game_loop(self, interval:float=0.02) -> None
```
Simulate the game world.

This function blocks as it continously progresses the game state through time
but it can also be spawned as a coroutine or in a thread via `run_game_loop_in_thread`.
As long as the simulation is running, the `GameStatus` will be `'Active'`.

#### Arguments
 - `interval`: (minimum) duration in seconds between consecutive time steps


### run_game_loop_in_thread
```python
GameStateMachine.run_game_loop_in_thread(self, interval:float=0.02) -> threading.Thread
```
Simulate the game in a seperate thread.

See `GameStateMachine.run_game_loop`.

#### Returns
the thread the game loop runs in


### stop
```python
GameStateMachine.stop(self, timeout:float=1.0) -> bool
```
Pause the game simulation.

This sets `status` to `Gamestatus.get('Paused')`. This method can also be spawned as a coroutine.
A subsequent call of `run_game_loop` will resume the simulation at the point where it was stopped.

### Returns
wether or not the simulation was successfully stopped


### time_step
```python
GameStateMachine.time_step(self, game_state:pygase.gamestate.GameState, dt:float) -> dict
```
Calculate a game state update.

This method should be implemented to return a dict with all the updated state attributes.

#### Arguments
 - `game_state`: the state of the game prior to the time step
 - `dt`: time in seconds since the last time step, use it to simulate at a consistent speed

#### Returns
a dict with updated game state attributes


