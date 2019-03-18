# -*- coding: utf-8 -*-

from pygase.utils import Sendable, NamedEnum

class Event(Sendable):

    def __init__(self, event_type:str, handler_args:tuple=()):
        self.type = event_type
        self.data = handler_args

class UniversalEventHandler:

    def __init__(self):
        self._event_handlers = {}

    def push_event_handler(self, event_type:str, event_handler):
        self._event_handlers[event_type] = event_handler

    async def handle_async(self, event:Event):
        await self._event_handlers[event.type](*event.data)

    def handle_blocking(self, event:Event):
        self._event_handlers[event.type](*event.data)
