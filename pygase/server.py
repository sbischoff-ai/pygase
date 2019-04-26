# -*- coding: utf-8 -*-
"""Serve PyGaSe clients.

Provides the `Server` class.

"""

import threading

import curio
from curio import socket
from curio.meta import awaitable

from pygase.connection import ServerConnection
from pygase.gamestate import GameStateStore
from pygase.event import UniversalEventHandler, Event


class Server:

    """Listen to clients and orchestrate the flow of events and state updates.

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

    """

    def __init__(self, game_state_store: GameStateStore):
        self.connections: dict = {}
        self.host_client: tuple = None
        self.game_state_store = game_state_store
        self._universal_event_handler = UniversalEventHandler()
        self._hostname: str = None
        self._port: int = None

    def run(self, port: int = 0, hostname: str = "localhost", event_wire=None) -> None:
        """Start the server under a specified address.

        This is a blocking function but can also be spawned as a coroutine or in a thread via `run_in_thread`.

        #### Arguments
         - `port`: port number the server will be bound to, default will be an available
           port chosen by the computers network controller
         - `hostname`: hostname or IP address the server will be bound to.
           Defaults to `'localhost'`.
         - `event_wire`: object to which events are to be repeated
           (has to implement a `_push_event(event)` method and is typically a `GameStateMachine`)

        """
        curio.run(self.run, port, hostname, event_wire)

    @awaitable(run)
    async def run(  # pylint: disable=function-redefined
        self, port: int = 0, hostname: str = "localhost", event_wire=None
    ) -> None:
        # pylint: disable=missing-docstring
        await ServerConnection.loop(hostname, port, self, event_wire)

    def run_in_thread(
        self, port: int = 0, hostname: str = "localhost", event_wire=None, daemon=True
    ) -> threading.Thread:
        """Start the server in a seperate thread.

        See `Server.run(port, hostname)`.

        #### Returns
        the thread the server loop runs in

        """
        thread = threading.Thread(target=self.run, args=(port, hostname, event_wire), daemon=daemon)
        thread.start()
        return thread

    @property
    def hostname(self) -> str:
        """Get the hostname or IP address on which the server listens.

        Returns `None` when the server is not running.

        """
        return "localhost" if self._hostname == "127.0.0.1" else self._hostname

    @property
    def port(self) -> int:
        """Get the port number on which the server listens.

        Returns `None` when the server is not running.

        """
        return self._port

    def shutdown(self) -> None:
        """Shut down the server.

        The server can be restarted via `run` in which case it will remember previous connections.
        This method can also be spawned as a coroutine.

        """
        curio.run(self.shutdown)

    @awaitable(shutdown)
    async def shutdown(self) -> None:  # pylint: disable=function-redefined
        # pylint: disable=missing-docstring
        async with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            await sock.sendto("shut_me_down".encode("utf-8"), (self._hostname, self._port))

    # advanced type checking for target client and callback would be helpful
    def dispatch_event(
        self, event_type: str, *args, target_client="all", retries: int = 0, ack_callback=None, **kwargs
    ) -> None:
        """Send an event to one or all clients.

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

        """
        event = Event(event_type, *args, **kwargs)

        def get_ack_callback(connection):
            return lambda: ack_callback(connection)

        if retries > 0:

            def get_timeout_callback(connection):
                return lambda: self.dispatch_event(
                    event_type, *args, connection=connection, retries=retries - 1, ack_callback=ack_callback, **kwargs
                )

        else:

            def get_timeout_callback(connection):  # pylint: disable=unused-argument
                return None

        if target_client == "all":
            for connection in self.connections.values():
                connection.dispatch_event(
                    event, get_ack_callback(connection), get_timeout_callback(connection), **kwargs
                )
        else:
            self.connections[target_client].dispatch_event(
                event,
                get_ack_callback(self.connections[target_client]),
                get_timeout_callback(self.connections[target_client]),
                **kwargs
            )

    # add advanced type checking for handler functions
    def register_event_handler(self, event_type: str, event_handler_function) -> None:
        """Register an event handler for a specific event type.

        #### Arguments
         - `event_type`: event type to link the handler function to
         - `handler_func`: function or coroutine to be invoked for events of the given type

        """
        self._universal_event_handler.register_event_handler(event_type, event_handler_function)
