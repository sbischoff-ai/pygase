# -*- coding: utf-8 -*-

import threading

import curio

from pygase.connection import ClientConnection
from pygase.event import UniversalEventHandler, Event

class Client:

    def __init__(self):
        self.connection = None
        self._universal_event_handler = UniversalEventHandler()

    async def connect_async(self, port:int, hostname:str='localhost'):
        self.connection = ClientConnection((hostname, port), self._universal_event_handler)
        await self.connection.loop()

    def connect_blocking(self, port:int, hostname:str='localhost'):
        self.connection = ClientConnection((hostname, port), self._universal_event_handler)
        curio.run(self.connection.loop)

    def connect_in_thread(self, port:int, hostname:str='localhost'):
        self.connection = ClientConnection((hostname, port), self._universal_event_handler)
        thread = threading.Thread(target=curio.run, args=(self.connection.loop,))
        thread.start()
        return thread

    def access_game_state(self):
        '''
        Returns a context manager to access the shared game state in a thread-safe way.

        Example:
        ```python
        with client.access_game_state() as game_state:
            do_stuff(game_state)
        ```
        '''
        return self.connection.game_state_context

    def dispatch_event(self, event_type:str, handler_args:list, retries:int=0, ack_callback=None):
        event = Event(event_type, handler_args)
        timeout_callback = None
        if retries > 0:
            timeout_callback = lambda: self.dispatch_event(
                event_type, handler_args,
                retries-1, ack_callback
            )
        self.connection.dispatch_event(event, ack_callback, timeout_callback)

    def push_event_handler(self, event_type:str, handler_func):
        self._universal_event_handler.push_event_handler(event_type, handler_func)
