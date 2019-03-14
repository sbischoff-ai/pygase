# -*- coding: utf-8 -*-

from pygase.utils import Sendable, NamedEnum, sqn

class EventType(NamedEnum):
    pass
EventType.register('ShutdownServer')

class Event(Sendable):

    _event_handlers = {}

    def __init__(self, event_type:int, data:tuple=()):
        self.type = event_type
        self.data = data

class UniversalEventHandler:

    _event_handlers = {}

    @classmethod
    def push_event_handler(cls, event_type, event_handler):
        cls._event_handlers[event_type] = event_handler

    @classmethod
    def handle(cls, event:Event):
        event_type = EventType.get(event.type)
        cls._event_handlers[event_type](*event.data)
