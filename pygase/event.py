# -*- coding: utf-8 -*-

from pygase.utils import Sendable, NamedEnum

class Event(Sendable):

    def __init__(self, event_type:str, handler_args:list=[], handler_kwargs:dict={}):
        self.type = event_type
        self.handler_args = handler_args
        self.handler_kwargs = handler_kwargs

class UniversalEventHandler:

    def __init__(self):
        self._event_handlers = {}

    def push_event_handler(self, event_type:str, event_handler):
        self._event_handlers[event_type] = event_handler

    async def handle_async(self, event:Event, **kwargs):
        return await self._event_handlers[event.type](*event.handler_args, **dict(event.handler_kwargs, **kwargs))

    def handle_blocking(self, event:Event, **kwargs):
        return self._event_handlers[event.type](*event.handler_args, **dict(event.handler_kwargs, **kwargs))

    def has_type(self, event_type:str):
        return event_type in self._event_handlers
