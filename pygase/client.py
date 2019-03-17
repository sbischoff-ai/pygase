# -*- coding: utf-8 -*-

import threading

import curio

from pygase.connection import ClientConnection
from pygase.event import UniversalEventHandler, Event, EventType

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

    def dispatch_event(self, event_name:str, data):
        event_type = EventType.get(event_name)
        self.connection.dispatch_event(Event(event_type, data))

    def push_event_handler(self, event_name:str, handler_func):
        event_type = EventType.get(event_name)
        self._universal_event_handler.push_event_handler(event_type, handler_func)
