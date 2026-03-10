# -*- coding: utf-8 -*-
"""Connect to PyGaSe servers.

# Contents
- #Client: main API class for PyGaSe clients

"""

import time
import threading
from collections.abc import Callable
from typing import Awaitable, Callable as TypingCallable, TypeVar, cast

from pygase.gamestate import GameState
from pygase.utils import LockedResource

from pygase import aio
from pygase.aio import awaitable

from pygase.connection import ClientConnection
from pygase.event import UniversalEventHandler, Event, EventHandler
from pygase.utils import logger

ReturnT = TypeVar("ReturnT")


class Client:
    """Exchange events with a PyGaSe server and access a synchronized game state.

    # Attributes
    connection (pygase.connection.ClientConnection): object that contains all networking information

    # Example
    ```python
    from time import sleep
    # Connect a client to the server from the Backend code example
    client = Client()
    client.connect_in_thread(hostname="localhost", port=8080)
    # Increase `bar` five times, then reset `foo`
    for i in range(5):
        client.dispatch_event("SET_BAR", new_bar=i)
        sleep(1)
    client.dispatch_event("RESET_FOO")
    ```

    """

    def __init__(self) -> None:
        logger.debug("Creating Client instance.")
        self.connection: ClientConnection | None = None
        self._universal_event_handler = UniversalEventHandler()

    def _require_connection(self) -> ClientConnection:
        if self.connection is None:
            raise RuntimeError("Client is not connected.")
        return self.connection

    def connect(self, port: int, hostname: str = "localhost") -> None:
        """Open a connection to a PyGaSe server.

        This is a blocking function but can also be spawned as a coroutine or in a thread
        via #Client.connect_in_thread().

        # Arguments
        port (int): port number of the server to which to connect
        hostname (str): hostname or IPv4 address of the server to which to connect

        """
        self.connection = ClientConnection((hostname, port), self._universal_event_handler)
        aio.run(self._require_connection().loop)

    @awaitable(connect)
    async def connect(self, port: int, hostname: str = "localhost") -> None:  # pylint: disable=function-redefined
        # pylint: disable=missing-docstring
        self.connection = ClientConnection((hostname, port), self._universal_event_handler)
        await cast(TypingCallable[[], Awaitable[None]], self._require_connection().loop)()

    def connect_in_thread(self, port: int, hostname: str = "localhost") -> threading.Thread:
        """Open a connection in a seperate thread.

        See #Client.connect().

        # Returns
        threading.Thread: the thread the client loop runs in

        """
        self.connection = ClientConnection((hostname, port), self._universal_event_handler)
        thread = threading.Thread(target=aio.run, args=(self._require_connection().loop,))
        thread.start()
        return thread

    def disconnect(self, shutdown_server: bool = False) -> None:
        """Close the client connection.

        This method can also be spawned as a coroutine.

        # Arguments
        shutdown_server (bool): whether or not the server should be shut down
            (only has an effect if the client has host permissions)

        """
        self._require_connection().shutdown(shutdown_server)

    @awaitable(disconnect)
    async def disconnect(self, shutdown_server: bool = False) -> None:  # pylint: disable=function-redefined
        # pylint: disable=missing-docstring
        await cast(TypingCallable[[bool], Awaitable[None]], self._require_connection().shutdown)(shutdown_server)

    def access_game_state(self) -> LockedResource[GameState]:
        """Return a context manager to access the shared game state.

        Can be used in a `with` block to lock the synchronized `game_state` while working with it.

        # Example
        ```python
        with client.access_game_state() as game_state:
            do_stuff(game_state)
        ```

        """
        return self._require_connection().game_state_context

    def wait_until(self, game_state_condition: Callable[[GameState], bool], timeout: float = 1.0) -> None:
        """Block until a condition on the game state is satisfied.

        # Arguments
        game_state_condition (callable): function that takes a #pygase.GameState instance and returns a bool
        timeout (float): time in seconds after which to raise a #TimeoutError

        # Raises
        TimeoutError: if the condition is not met after `timeout` seconds

        """
        condition_satisfied = False
        t0 = time.time()
        while not condition_satisfied:
            with self.access_game_state() as game_state:
                if game_state_condition(game_state):
                    condition_satisfied = True
            if time.time() - t0 > timeout:
                raise TimeoutError("Condition not satisfied after timeout of " + str(timeout) + " seconds.")
            time.sleep(timeout / 100)

    def try_to(self, function: Callable[[GameState], ReturnT], timeout: float = 1.0) -> ReturnT:
        """Execute a function using game state attributes that might not yet exist.

        This method repeatedly tries to execute `function(game_state)`, ignoring #KeyError exceptions,
        until it either works or times out.

        # Arguments
        function (callable): function that takes a #pygase.GameState instance and returns anything
        timeout (float): time in seconds after which to raise a #TimeoutError

        # Returns
        any: whatever `function(game_state)` returns

        # Raises
        TimeoutError: if the function doesn't run through after `timeout` seconds

        """
        result = None
        t0 = time.time()
        while True:
            with self.access_game_state() as game_state:
                try:
                    result = function(game_state)
                except (KeyError, AttributeError):
                    pass
            if result is not None:
                return result
            if time.time() - t0 > timeout:
                raise TimeoutError("Condition not satisfied after timeout of " + str(timeout) + " seconds.")
            time.sleep(timeout / 100)

    def dispatch_event(
        self,
        event_type: str,
        *args: object,
        retries: int = 0,
        ack_callback: EventHandler | None = None,
        **kwargs: object,
    ) -> None:
        """Send an event to the server.

        # Arguments
        event_type (str): event type identifier that links to a handler
        retries (int): number of times the event is to be resent in case it times out
        ack_callback (callable, coroutine): will be invoked after the event was received

        Additional positional and keyword arguments will be sent as event data and passed to the handler function.

        ---
        `ack_callback` should not perform any long-running blocking operations (say a `while True` loop), as that will
        block the connections asynchronous event loop. Use a coroutine instead, with appropriately placed `await`s.

        """
        event = Event(event_type, *args, **kwargs)
        if retries > 0:

            def timeout_callback() -> None:
                self.dispatch_event(event_type, *args, retries=retries - 1, ack_callback=ack_callback, **kwargs)
                logger.warning(f"Event of type {event_type} timed out. Retrying to send event to server.")

        else:
            timeout_callback = None

        self._require_connection().dispatch_event(event, ack_callback, timeout_callback)

    def register_event_handler(self, event_type: str, event_handler_function: EventHandler) -> None:
        """Register an event handler for a specific event type.

        # Arguments
        event_type (str): event type to link the handler function to
        handler_func (callable, coroutine): will be called for events of the given type

        """
        self._universal_event_handler.register_event_handler(event_type, event_handler_function)
