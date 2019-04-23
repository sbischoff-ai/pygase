# -*- coding: utf-8 -*-
'''
Provides all PyGaSe components that deal with game states and state progression.
'''

import time
import threading

import curio
from curio.meta import awaitable

from pygase.utils import Sendable, NamedEnum, sqn
from pygase.event import UniversalEventHandler

# unique 4-byte token to mark GameState entries for deletion
TO_DELETE = bytes.fromhex('d281e5ba')

class GameStatus(NamedEnum): pass
GameStatus.register('Paused')
GameStatus.register('Active')

class GameState(Sendable):
    '''
    Contains game state information that is required to be known both by the server and the client.
    Since it is a *Sendable*, it can only contain attributes of type `str`, `bytes`, `sqn`, `int`, `float`,
    `bool` as well as `list`s or `tuple`s of such.

    ### Optional Arguments
     - **time_order** *int/sqn*: current time order number of the game state, higher means more recent
     - **game_status** *str*: **GameStatus** enum value that basically describes whether or not the game loop is running
     - **kwargs** *dict*: keyword arguments that describe custom game state attributes
    
    ### Attributes
      **GameState** instances mainly consist of custom attributes that make up the game state
      - **game_status** *str*: **GameStatus** enum `'Paused'` or `'Active'`
      - **time_order** *int/sqn*: current time order number of the game state, the higher the more recent
    '''

    def __init__(self, time_order:int=0, game_status:str=GameStatus.get('Paused'), **kwargs):
        self.__dict__ = kwargs
        self.game_status = game_status
        self.time_order = sqn(time_order)

    def is_paused(self):
        '''
        ### Returns
          `True` if game status is `'Paused'`.
        '''
        return self.game_status == GameStatus.get('Paused')

    # Check time ordering
    def __lt__(self, other):
        return self.time_order < other.time_order

    def __gt__(self, other):
        return self.time_order > other.time_order


class GameStateUpdate(Sendable):
    '''
    Represents a set of changes to carry out on a *GameState*.
    The server keeps a *time_order* counter and labels all updates in ascending order.

    Keywords are *GameState* attribute names. If you want to remove some key from the
    game state (*GameState* attributes themselves can also be deleted, which removes them from
    the object altogether), just assign *TO_DELETE* to it in the update.

    Use the *+* operator to add *GameStateUpdate*s together or to add them to a
    *GameState* (returning the updated update/state).

    Adding up available updates will always result in an equally or more current but
    also heavier update (meaning it will contain more data).

    ### Arguments
     - **time_order** *int/sqn*: the time order up to which the update reaches
     - **kwargs** *dict*: the game state attributes to be updated
    
    ### Attributes
    **GameStateUpdate** instances mainly consist of custom game state attributes to update.
     - **time_order** *sqn*: the time order up to which the update reaches
    '''

    def __init__(self, time_order:int, **kwargs):
        self.__dict__ = kwargs
        self.time_order = sqn(time_order)

    @classmethod
    def from_bytes(cls, bytepack:bytes):
        '''
        ### Arguments
         - **bytepack** *bytes*: the bytestring to be parsed to a **GameStateUpdate**
        
        ### Returns
          A copy of the update that was packed into byte format
        '''
        update = super().from_bytes(bytepack)
        update.time_order = sqn(update.time_order) # pylint: disable=no-member
        return update

    # Adding to another update should return an updated update
    def __add__(self, other):
        if other > self:
            _recursive_update(self.__dict__, other.__dict__)
            return self
        else:
            _recursive_update(other.__dict__, self.__dict__)
            return other

    # Adding to a GameState should update and return the state
    def __radd__(self, other):
        if type(other) is int:
            # This is so that sum() works on lists of updates, because
            # sum will always begin by adding the first element of the
            # list to 0.
            return self
        if self > other:
            _recursive_update(other.__dict__, self.__dict__, delete=True)
        return other

    # Check time ordering
    def __lt__(self, other):
        return self.time_order < other.time_order

    def __gt__(self, other):
        return self.time_order > other.time_order

# This is for GameStateUpdate objects, which should update nested
# dicts recursively so that no state data is unexpectedly deleted.
# Also, this functions manages deletion of state objects.
def _recursive_update(d: dict, u: dict, delete=False):
    for k, v in u.items():
        if v == TO_DELETE and delete and k in d.keys():
            del d[k]
        elif isinstance(v, dict) and k in d.keys() and isinstance(d[k], dict):
            _recursive_update(d[k], v, delete=delete)
        else:
            d[k] = v

class GameStateStore:
    '''
    An interface for the part of the PyGaSe backend that provides access to the game state.

    ### Optional Arguments
     - **inital_game_state** *GameState*: state of the game before state progression begins
    '''
    _update_cache_size = 100

    def __init__(self, initial_game_state:GameState=GameState()):
        self._game_state = initial_game_state
        self._game_state_update_cache = [GameStateUpdate(0)]

    def get_update_cache(self):
        '''
        ### Returns
          A list of all the recent **GameStateUpdate*s, up to the state stores cache size
        '''
        return self._game_state_update_cache.copy()

    def get_game_state(self):
        '''
        ### Returns
          The current game state
        '''
        return self._game_state

    def push_update(self, update:GameStateUpdate):
        '''
        This method will usually be called by whatever is progressing the game state, usually a
        **GameStateMachine**.

        ### Arguments
          **update** *GameStateUpdate*: a new update that is to be applied to the state
        '''
        self._game_state_update_cache.append(update)
        if len(self._game_state_update_cache) > self._update_cache_size:
            del self._game_state_update_cache[0]
        if update > self._game_state:
            self._game_state += update

class GameStateMachine:
    '''
    A class providing the means to progress a game state through time, applying all game simulation logic.
    This class is meant either as a base class from which you inherit and implement the `time_step` method,
    or you assign an implementation after instantiation.

    ### Arguments
     - **game_state_store** *GameStateStore*: part of the backend that provides the state
    
    ### Attributes
     - **game_time** *float*: duration the game has been running in seconds
    '''
    def __init__(self, game_state_store:GameStateStore):
        self.game_time = 0.0
        self._event_queue = curio.UniversalQueue()
        self._universal_event_handler = UniversalEventHandler()
        self._game_state_store = game_state_store
        self._game_loop_is_running = False

    def _push_event(self, update_dict:dict):
        self._event_queue.put(update_dict)

    @awaitable(_push_event)
    async def _push_event(self, update_dict:dict): #pylint: disable=function-redefined
        await self._event_queue.put(update_dict)

    def push_event_handler(self, event_type:str, handler_func):
        '''
        For event handlers to have any effect, the events have to be wired from a **Server** to the
        **GameStateMachine**.

        ### Arguments
         - **event_type** *str*: event type to link the handler function to
         - **handler_func**: function or coroutine to be invoked for events of the given type,
            gets passed the keyword argument `game_state` (along with those attached
            to the event) and is expected to return an update dict
        '''
        self._universal_event_handler.push_event_handler(event_type, handler_func)

    def run_game_loop(self, interval:float=0.02):
        '''
        Runs the simulation that progresses the game state through time. (Can also be called as a coroutine.)
        As long as the simulation is running, the **GameStatus** will be `'Active'`.

        ### Arguments
         - **interval** *float*: (minimum) duration in seconds between consecutive time steps
        '''
        curio.run(self.run_game_loop, interval)

    @awaitable(run_game_loop)
    async def run_game_loop(self, interval:float=0.02): #pylint: disable=function-redefined
        if self._game_state_store.get_game_state().game_status == GameStatus.get('Paused'):
            self._game_state_store.push_update(
                GameStateUpdate(
                    self._game_state_store.get_game_state().time_order + 1,
                    game_status=GameStatus.get('Active')
                )
            )
        game_state = self._game_state_store.get_game_state()
        dt = interval
        self._game_loop_is_running = True
        while game_state.game_status == GameStatus.get('Active'):
            t0 = time.time()
            update_dict = self.time_step(game_state, dt)
            while not self._event_queue.empty():
                event = await self._event_queue.get()
                event_update = self._universal_event_handler.handle_blocking(event, game_state=game_state, dt=dt)
                update_dict.update(event_update)
                if time.time() - t0 > 0.95*interval:
                    break
            self._game_state_store.push_update(GameStateUpdate(game_state.time_order + 1, **update_dict))
            game_state = self._game_state_store.get_game_state()
            dt = max(interval, time.time()-t0)
            await curio.sleep(max(0, interval-dt))
            self.game_time += dt
        self._game_loop_is_running = False

    def run_game_loop_in_thread(self, interval:float=0.02):
        '''
        Simulate the game in a seperate thread.

        See **GameStateMachine.run_game_loop(interval)**.

        ### Returns
        *threading.Thread*: the thread the game loop runs in
        '''
        thread = threading.Thread(target=self.run_game_loop, args=(interval,))
        thread.start()
        return thread

    def stop(self, timeout:float=1.0):
        '''
        Stops the game simulation, setting its **GameStatus** to `'Paused'`. (Can also be called as a coroutine.)

        A subsequent call of `run_game_loop` will resume the simulation at the point where it was stopped.
        '''
        return curio.run(self.stop, timeout)

    @awaitable(stop)
    async def stop(self, timeout:float=1.0): # pylint: disable=function-redefined
        if self._game_state_store.get_game_state().game_status == GameStatus.get('Active'):
            self._game_state_store.push_update(
                GameStateUpdate(
                    self._game_state_store.get_game_state().time_order + 1,
                    game_status=GameStatus.get('Paused')
                )
            )
        t0 = time.time()
        while self._game_loop_is_running:
            if time.time() - t0 > timeout:
                break
            await curio.sleep(0)
        return not self._game_loop_is_running

    def time_step(self, game_state:GameState, dt):
        '''
        This method should be implemented to return a dict with all the updated state attributes.

        ### Arguments
         - **game_state** *GameState*: the state of the game prior to the time step
         - **dt** *float*: time in seconds since the last time step, use it to simulate at a consistent speed
        
        ### Returns
          A dict with all the game state attributes that have to be updated due to the time step
        '''
        raise NotImplementedError()
