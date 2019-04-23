# -*- coding: utf-8 -*-
'''
Contains the basic components of the Pygase event framework.
'''

from curio.meta import iscoroutinefunction

from pygase.utils import Sendable, NamedEnum

class Event(Sendable):
    '''
    ### Arguments
     - **event_type** *str*: string that identifies the event and links it to a handler
    
    ### Optional Arguments
     - **handler_args** *list*: list of positional arguments to be passed to the handler function that will be invoked
       on the other side of the connection
     - **handler_kwargs** *dict*: dict of keyword arguments to be passed to the handler function
    
    ### Attributes
     - **type** *str*
     - **handler_args** *list*
     - **handler_kwargs** *dict*
    '''
    def __init__(self, event_type:str, handler_args:list=[], handler_kwargs:dict={}):
        self.type = event_type
        self.handler_args = handler_args
        self.handler_kwargs = handler_kwargs

class UniversalEventHandler:
    '''
    Deals with event handling and is usually part of a PyGaSe connection.
    '''
    def __init__(self):
        self._event_handlers = {}

    def push_event_handler(self, event_type:str, event_handler_function):
        '''
        ### Arguments
         - **event_type** *str*: string that identifies the events to be handles by this function
         - **event_handler_function**: callbackfunction that will be invoked with the handler args 
           and kwargs with which the incoming event has been dispatched (can also be a coroutine)
        '''
        self._event_handlers[event_type] = event_handler_function

    async def handle(self, event:Event, **kwargs):
        '''
        calls the appropriate handler function

        ### Arguments
         - **event** *Event*: the event to be handled
        
        ### Optional Arguments
         - **kwargs** *dict*: additional keyword arguments to be passed to the handler function
        '''
        if iscoroutinefunction(self._event_handlers[event.type]):
            return await self._event_handlers[event.type](*event.handler_args, **dict(event.handler_kwargs, **kwargs))
        else:
            return self._event_handlers[event.type](*event.handler_args, **dict(event.handler_kwargs, **kwargs))

    def has_type(self, event_type:str):
        '''
        ### Arguments
         - **event_type** *str*: event type for which to check
        
        ### Returns
         `True` if a handler has been pushed for the given event type, `False` otherwise
        '''
        return event_type in self._event_handlers
