# -*- coding: utf-8 -*-

from pygase.utils import Sendable, NamedEnum

class EventType(NamedEnum):
    pass

class Event(Sendable):

    def __init__(self, event_type:int, data:tuple=()):
        self.type = event_type
        self.data = data

class UniversalEventHandler:

    def __init__(self):
        self._event_handlers = {}

    def push_event_handler(self, event_type:int, event_handler):
        self._event_handlers[event_type] = event_handler

    async def handle_async(self, event:Event):
        await self._event_handlers[event.type](*event.data)

    def handle_blocking(self, event:Event):
        event_type = EventType.get(event.type)
        self._event_handlers[event_type](*event.data)
