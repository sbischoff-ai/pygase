# -*- coding: utf-8 -*-
import threading

import curio

from pygase.connection import ServerConnection
from pygase.gamestate import GameStateStore, GameStateMachine
from pygase.event import UniversalEventHandler, Event

class Server:
    
    def __init__(self, game_state_store:GameStateStore=GameStateStore()):
        self.connections = {}
        self._universal_event_handler = UniversalEventHandler()
        self.game_state_store = game_state_store

    async def run_async(self, port:int=0, hostname:str='localhost'):
        await ServerConnection.loop(
            hostname, port,
            self.connections,
            self._universal_event_handler,
            self.game_state_store
        )

    def run_blocking(self, port:int=0, hostname:str='localhost'):
        curio.run(
            ServerConnection.loop,
            hostname, port,
            self.connections,
            self._universal_event_handler,
            self.game_state_store
        )

    def run_in_thread(self, port:int=0, hostname:str='localhost'):
        thread = threading.Thread(
            target=curio.run,
            args=(
                ServerConnection.loop,
                hostname, port,
                self.connections,
                self._universal_event_handler,
                self.game_state_store
            )
        )
        thread.start()
        return thread

    def dispatch_event(self, event_type:str, handler_args:list, target_client='all', retries:int=0, ack_callback=None):
        '''
        ack_callback will be passed a reference to the client connection
        '''
        event = Event(event_type, handler_args)
        def get_ack_callback(connection): return lambda: ack_callback(connection)
        if retries > 0:
            def get_timeout_callback(connection):
                return lambda: self.dispatch_event(
                    event_type, handler_args,
                    connection,
                    retries-1, ack_callback
                )
        else:
            def get_timeout_callback(connection): return None
        if target_client == 'all':
            for connection in self.connections.values():
                connection.dispatch_event(
                    event,
                    get_ack_callback(connection),
                    get_timeout_callback(connection)
                )
        else:
            self.connections[target_client].dispatch_event(
                event,
                get_ack_callback(self.connections[target_client]),
                get_timeout_callback(self.connections[target_client])
            )

    def push_event_handler(self, event_type:str, handler_func):
        self._universal_event_handler.push_event_handler(event_type, handler_func)
