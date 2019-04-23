# -*- coding: utf-8 -*-
'''
Provides the **Client** class.
'''

import threading

import curio
from curio.meta import awaitable

from pygase.connection import ClientConnection
from pygase.event import UniversalEventHandler, Event

class Client:
    '''
    #### Attributes
     - **connection** *ClientConnection*: object that contains all networking information
    '''
    def __init__(self):
        self.connection = None
        self._universal_event_handler = UniversalEventHandler()

    def connect(self, port:int, hostname:str='localhost'):
        '''
        Open a connection to a PyGaSe server. (Can be called as a coroutine.)

        #### Arguments
         - **port** *int*: port number of the server to which to connect
        
        #### Optional Arguments
         - **hostname** *str*: hostname of the server to which to connect
        '''
        self.connection = ClientConnection((hostname, port), self._universal_event_handler)
        curio.run(self.connection.loop)

    @awaitable(connect)
    async def connect(self, port:int, hostname:str='localhost'): #pylint: disable=function-redefined
        self.connection = ClientConnection((hostname, port), self._universal_event_handler)
        await self.connection.loop()

    def connect_in_thread(self, port:int, hostname:str='localhost'):
        '''
        Open a connection in a seperate thread.

        See **Client.connect(port, hostname)**.

        #### Returns
        *threading.Thread*: the thread the client loop runs in
        '''
        self.connection = ClientConnection((hostname, port), self._universal_event_handler)
        thread = threading.Thread(target=curio.run, args=(self.connection.loop,))
        thread.start()
        return thread

    def disconnect(self, shutdown_server:bool=False):
        '''
        Close the client connection. (Can also be called as a coroutine.)

        #### Optional Arguments
         - **shutdown_server** *bool*: wether or not the server should be shut down.
            (Only has an effect if the client has host permissions.)
        '''
        self.connection.shutdown(shutdown_server)

    @awaitable(disconnect)
    async def disconnect(self, shutdown_server:bool=False): #pylint: disable=function-redefined
        await self.connection.shutdown(shutdown_server)

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

    def dispatch_event(self, event_type:str, handler_args:list=[], retries:int=0, ack_callback=None, **kwargs):
        '''
        Sends an event to the server.

        #### Arguments
         - **event_type** *str*: string that identifies the event and links it to a handler
        
        #### Optional Arguments
         - **handler_args** *list*: list of positional arguments to be passed to the handler function that will be invoked
           by the server
         - **retries** *int*: number of times the event is to be resent, in the case it times out
         - **ack_callback**: function or coroutine to be executed after the event was received
         - **kwargs** *dict*: keyword arguments to be passed to the handler function
        '''
        event = Event(event_type, handler_args, kwargs)
        timeout_callback = None
        if retries > 0:
            timeout_callback = lambda: self.dispatch_event(
                event_type, handler_args,
                retries-1, ack_callback,
                **kwargs
            )
        self.connection.dispatch_event(event, ack_callback, timeout_callback)

    def push_event_handler(self, event_type:str, handler_func):
        '''
        #### Arguments
         - **event_type** *str*: event type to link the handler function to
         - **handler_func**: function or coroutine to be invoked for events of the given type
        '''
        self._universal_event_handler.push_event_handler(event_type, handler_func)
