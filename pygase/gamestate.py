# -*- coding: utf-8 -*-
"""
Provides all PyGaSe components that deal with game states and state progression.
"""

import time
import threading

import curio
from curio.meta import awaitable

from pygase.utils import Sendable, NamedEnum, Sqn
from pygase.event import UniversalEventHandler, Event

# unique 4-byte token to mark GameState entries for deletion
TO_DELETE: bytes = bytes.fromhex("d281e5ba")


class GameStatus(NamedEnum):
    """
    Enum for the game simulation status:
     - `'Paused'`
     - `'Active'`

    """


GameStatus.register("Paused")
GameStatus.register("Active")


class GameState(Sendable):

    """Customize a serializable game state model.

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

    """

    def __init__(self, time_order: int = 0, game_status: int = GameStatus.get("Paused"), **kwargs):
        self.__dict__ = kwargs
        self.game_status = game_status
        self.time_order = Sqn(time_order)

    def is_paused(self) -> bool:
        """Return `True` if game is paused."""
        return self.game_status == GameStatus.get("Paused")

    # Check time ordering
    def __lt__(self, other) -> bool:
        return self.time_order < other.time_order

    def __gt__(self, other) -> bool:
        return self.time_order > other.time_order


class GameStateUpdate(Sendable):

    """Update a `GameState` object.

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

    """

    def __init__(self, time_order: int, **kwargs):
        self.__dict__ = kwargs
        self.time_order = Sqn(time_order)

    @classmethod
    def from_bytes(cls, bytepack: bytes) -> "GameStateUpdate":
        """Extend `Sendable.from_bytes` to make sure time_order is of type `Sqn`."""
        update = super().from_bytes(bytepack)
        update.time_order = Sqn(update.time_order)  # pylint: disable=no-member
        return update

    def __add__(self, other: "GameStateUpdate") -> "GameStateUpdate":
        """Combine two updates."""
        if other > self:
            _recursive_update(self.__dict__, other.__dict__)
            return self
        _recursive_update(other.__dict__, self.__dict__)
        return other

    def __radd__(self, other):
        """Update a `GameState`."""
        if isinstance(other, int):
            # This is so that sum() works on lists of updates, because
            # sum will always begin by adding the first element of the
            # list to 0.
            return self
        if self > other:
            _recursive_update(other.__dict__, self.__dict__, delete=True)
        return other

    # Check time ordering
    def __lt__(self, other) -> bool:
        return self.time_order < other.time_order

    def __gt__(self, other) -> bool:
        return self.time_order > other.time_order


def _recursive_update(my_dict: dict, update_dict: dict, delete: bool = False) -> None:
    """Update nested dicts deeply via recursion."""
    for key, value in update_dict.items():
        if value == TO_DELETE and delete and key in my_dict.keys():
            del my_dict[key]
        elif isinstance(value, dict) and key in my_dict.keys() and isinstance(my_dict[key], dict):
            _recursive_update(my_dict[key], value, delete=delete)
        else:
            my_dict[key] = value


class GameStateStore:

    """Provide access to a game state and manage state updates.

    #### Optional Arguments
     - `inital_game_state`: state of the game before the simulation begins

    """

    _update_cache_size: int = 100

    def __init__(self, initial_game_state: GameState = GameState()):
        self._game_state = initial_game_state
        self._game_state_update_cache = [GameStateUpdate(0)]

    def get_update_cache(self) -> list:
        """Return the latest state updates."""
        return self._game_state_update_cache.copy()

    def get_game_state(self) -> GameState:
        """Return the current game state."""
        return self._game_state

    def push_update(self, update: GameStateUpdate) -> None:
        """Push a new state update to the update cache.

        This method will usually be called by whatever is progressing the game state, usually a
        `GameStateMachine`.

        """
        self._game_state_update_cache.append(update)
        if len(self._game_state_update_cache) > self._update_cache_size:
            del self._game_state_update_cache[0]
        if update > self._game_state:
            self._game_state += update


class GameStateMachine:

    """Run a simulation that propagates the game state.

    A `GameStateMachine` progresses a game state through time, applying all game simulation logic.
    This class is meant either as a base class from which you inherit and implement the `time_step` method,
    or you assign a `time_step` implementation after instantiation.

    #### Arguments
     - `game_state_store`: part of the PyGaSe backend that provides the state

    #### Attributes
     - `game_time`: duration the game has been running in seconds

    """

    def __init__(self, game_state_store: GameStateStore):
        self.game_time: float = 0.0
        self._event_queue = curio.UniversalQueue()
        self._universal_event_handler = UniversalEventHandler()
        self._game_state_store = game_state_store
        self._game_loop_is_running = False

    def _push_event(self, event: Event) -> None:
        """Push an event into the state machines event queue.

        This method can be spawned as a coroutine.

        """
        self._event_queue.put(event)

    @awaitable(_push_event)
    async def _push_event(self, event: Event) -> None:  # pylint: disable=function-redefined
        await self._event_queue.put(event)

    # advanced type checking for the handler function would be helpful
    def register_event_handler(self, event_type: str, event_handler_function) -> None:
        """Register an event handler for a specific event type.

        For event handlers to have any effect, the events have to be wired from a `Server` to the
        `GameStateMachine` via the `event_wire` argument of the servers `run` method.

        #### Arguments
         - `event_type`: which type of event to link the handler function to
         - `handler_func`: function or coroutine to be invoked for events of the given type,
            gets passed the keyword argument `game_state` (along with those attached
            to the event) and is expected to return an update dict

        """
        self._universal_event_handler.register_event_handler(event_type, event_handler_function)

    def run_game_loop(self, interval: float = 0.02) -> None:
        """Simulate the game world.

        This function blocks as it continously progresses the game state through time
        but it can also be spawned as a coroutine or in a thread via `run_game_loop_in_thread`.
        As long as the simulation is running, the `GameStatus` will be `'Active'`.

        #### Arguments
         - `interval`: (minimum) duration in seconds between consecutive time steps

        """
        curio.run(self.run_game_loop, interval)

    @awaitable(run_game_loop)
    async def run_game_loop(self, interval: float = 0.02) -> None:  # pylint: disable=function-redefined
        # pylint: disable=missing-docstring
        if self._game_state_store.get_game_state().game_status == GameStatus.get("Paused"):
            self._game_state_store.push_update(
                GameStateUpdate(
                    self._game_state_store.get_game_state().time_order + 1, game_status=GameStatus.get("Active")
                )
            )
        game_state = self._game_state_store.get_game_state()
        dt = interval
        self._game_loop_is_running = True
        while game_state.game_status == GameStatus.get("Active"):
            t0 = time.time()
            update_dict = self.time_step(game_state, dt)
            while not self._event_queue.empty():
                event = await self._event_queue.get()
                event_update = await self._universal_event_handler.handle(event, game_state=game_state, dt=dt)
                update_dict.update(event_update)
                if time.time() - t0 > 0.95 * interval:
                    break
            self._game_state_store.push_update(GameStateUpdate(game_state.time_order + 1, **update_dict))
            game_state = self._game_state_store.get_game_state()
            dt = max(interval, time.time() - t0)
            await curio.sleep(max(0, interval - dt))
            self.game_time += dt
        self._game_loop_is_running = False

    def run_game_loop_in_thread(self, interval: float = 0.02) -> threading.Thread:
        """Simulate the game in a seperate thread.

        See `GameStateMachine.run_game_loop`.

        #### Returns
        the thread the game loop runs in

        """
        thread = threading.Thread(target=self.run_game_loop, args=(interval,))
        thread.start()
        return thread

    def stop(self, timeout: float = 1.0) -> bool:
        """Pause the game simulation.

        This sets `status` to `Gamestatus.get('Paused')`. This method can also be spawned as a coroutine.
        A subsequent call of `run_game_loop` will resume the simulation at the point where it was stopped.

        ### Returns
        wether or not the simulation was successfully stopped

        """
        return curio.run(self.stop, timeout)

    @awaitable(stop)
    async def stop(self, timeout: float = 1.0) -> bool:  # pylint: disable=function-redefined
        # pylint: disable=missing-docstring
        if self._game_state_store.get_game_state().game_status == GameStatus.get("Active"):
            self._game_state_store.push_update(
                GameStateUpdate(
                    self._game_state_store.get_game_state().time_order + 1, game_status=GameStatus.get("Paused")
                )
            )
        t0 = time.time()
        while self._game_loop_is_running:
            if time.time() - t0 > timeout:
                break
            await curio.sleep(0)
        return not self._game_loop_is_running

    def time_step(self, game_state: GameState, dt: float) -> dict:
        """Calculate a game state update.

        This method should be implemented to return a dict with all the updated state attributes.

        #### Arguments
         - `game_state`: the state of the game prior to the time step
         - `dt`: time in seconds since the last time step, use it to simulate at a consistent speed

        #### Returns
        a dict with updated game state attributes

        """
        raise NotImplementedError()
