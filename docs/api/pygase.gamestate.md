# pygase

PyGaSe, or Python Game Service, is a library (or framework, whichever name you prefer) that provides
a complete set of high-level components for real-time networking for games.

# pygase.gamestate

Provides all PyGaSe components that deal with game states and state progression.

## GameState
```python
GameState(self, time_order:int=0, game_status:str=0, **kwargs)
```

Contains game state information that is required to be known both by the server and the client.
Since it is a *Sendable*, it can only contain attributes of type `str`, `bytes`, `sqn`, `int`, `float`,
`bool` as well as `list`s or `tuple`s of such.

#### Optional Arguments
 - **time_order** *int/sqn*: current time order number of the game state, higher means more recent
 - **game_status** *str*: **GameStatus** enum value that basically describes whether or not the game loop is running
 - **kwargs** *dict*: keyword arguments that describe custom game state attributes

#### Attributes
  **GameState** instances mainly consist of custom attributes that make up the game state
  - **game_status** *str*: **GameStatus** enum `'Paused'` or `'Active'`
  - **time_order** *int/sqn*: current time order number of the game state, the higher the more recent

### is_paused
```python
GameState.is_paused(self)
```

#### Returns
  `True` if game status is `'Paused'`.

## GameStateUpdate
```python
GameStateUpdate(self, time_order:int, **kwargs)
```

Represents a set of changes to carry out on a *GameState*.
The server keeps a *time_order* counter and labels all updates in ascending order.

Keywords are *GameState* attribute names. If you want to remove some key from the
game state (*GameState* attributes themselves can also be deleted, which removes them from
the object altogether), just assign *TO_DELETE* to it in the update.

Use the *+* operator to add *GameStateUpdate*s together or to add them to a
*GameState* (returning the updated update/state).

Adding up available updates will always result in an equally or more current but
also heavier update (meaning it will contain more data).

#### Arguments
 - **time_order** *int/sqn*: the time order up to which the update reaches
 - **kwargs** *dict*: the game state attributes to be updated

#### Attributes
**GameStateUpdate** instances mainly consist of custom game state attributes to update.
 - **time_order** *sqn*: the time order up to which the update reaches

### from_bytes
```python
GameStateUpdate.from_bytes(bytepack:bytes)
```

#### Arguments
 - **bytepack** *bytes*: the bytestring to be parsed to a **GameStateUpdate**

#### Returns
  A copy of the update that was packed into byte format

## GameStateStore
```python
GameStateStore(self, initial_game_state:pygase.gamestate.GameState=<pygase.gamestate.GameState object at 0x000001D4690637F0>)
```

An interface for the part of the PyGaSe backend that provides access to the game state.

#### Optional Arguments
 - **inital_game_state** *GameState*: state of the game before state progression begins

### get_update_cache
```python
GameStateStore.get_update_cache(self)
```

#### Returns
  A list of all the recent **GameStateUpdate*s, up to the state stores cache size

### get_game_state
```python
GameStateStore.get_game_state(self)
```

#### Returns
  The current game state

### push_update
```python
GameStateStore.push_update(self, update:pygase.gamestate.GameStateUpdate)
```

This method will usually be called by whatever is progressing the game state, usually a
**GameStateMachine**.

#### Arguments
  **update** *GameStateUpdate*: a new update that is to be applied to the state

## GameStateMachine
```python
GameStateMachine(self, game_state_store:pygase.gamestate.GameStateStore)
```

A class providing the means to progress a game state through time, applying all game simulation logic.
This class is meant either as a base class from which you inherit and implement the `time_step` method,
or you assign an implementation after instantiation.

#### Arguments
 - **game_state_store** *GameStateStore*: part of the backend that provides the state

#### Attributes
 - **game_time** *float*: duration the game has been running in seconds

### push_event_handler
```python
GameStateMachine.push_event_handler(self, event_type:str, handler_func)
```

For event handlers to have any effect, the events have to be wired from a **Server** to the
**GameStateMachine**.

#### Arguments
 - **event_type** *str*: event type to link the handler function to
 - **handler_func**: function or coroutine to be invoked for events of the given type,
    gets passed the keyword argument `game_state` (along with those attached
    to the event) and is expected to return an update dict

### run_game_loop
```python
GameStateMachine.run_game_loop(self, interval:float=0.02)
```

Runs the simulation that progresses the game state through time. (Can also be called as a coroutine.)
As long as the simulation is running, the **GameStatus** will be `'Active'`.

#### Arguments
 - **interval** *float*: (minimum) duration in seconds between consecutive time steps

### run_game_loop_in_thread
```python
GameStateMachine.run_game_loop_in_thread(self, interval:float=0.02)
```

Simulate the game in a seperate thread.

See **GameStateMachine.run_game_loop(interval)**.

#### Returns
*threading.Thread*: the thread the game loop runs in

### stop
```python
GameStateMachine.stop(self, timeout:float=1.0)
```

Stops the game simulation, setting its **GameStatus** to `'Paused'`. (Can also be called as a coroutine.)

A subsequent call of `run_game_loop` will resume the simulation at the point where it was stopped.

### time_step
```python
GameStateMachine.time_step(self, game_state:pygase.gamestate.GameState, dt)
```

This method should be implemented to return a dict with all the updated state attributes.

#### Arguments
 - **game_state** *GameState*: the state of the game prior to the time step
 - **dt** *float*: time in seconds since the last time step, use it to simulate at a consistent speed

#### Returns
  A dict with all the game state attributes that have to be updated due to the time step

