# -*- coding: utf-8 -*-
import threading

import curio

from pygase.connection import ServerConnection
from pygase.event import UniversalEventHandler, Event, EventType

class Server:
    
    def __init__(self):
        self.connections = {}
        self._universal_event_handler = UniversalEventHandler()

    async def run_async(self, port:int=0, hostname:str='localhost'):
        await ServerConnection.loop(hostname, port, self.connections, self._universal_event_handler)

    def run_blocking(self, port:int=0, hostname:str='localhost'):
        curio.run(ServerConnection.loop, hostname, port, self.connections, self._universal_event_handler)

    def run_in_thread(self, port:int=0, hostname:str='localhost'):
        thread = threading.Thread(
            target=curio.run,
            args=(ServerConnection.loop, hostname, port, self.connections, self._universal_event_handler)
        )
        thread.start()
        return thread

    def dispatch_event(self, event_name:str, data, target_client='all'):
        event_type = EventType.get(event_name)
        event = Event(event_type, data)
        if target_client == 'all':
            for connection in self.connections:
                connection.dispatch_event(event)
        else:
            self.connections[target_client].dispatch_event(event)

    def push_event_handler(self, event_name:str, handler_func):
        event_type = EventType.get(event_name)
        self._universal_event_handler.push_event_handler(event_type, handler_func)
