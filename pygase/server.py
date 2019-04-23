# -*- coding: utf-8 -*-
'''
Provides the **Server** class.
'''

import threading

import curio
from curio import socket
from curio.meta import awaitable

from pygase.connection import ServerConnection
from pygase.gamestate import GameStateStore, GameStateMachine
from pygase.event import UniversalEventHandler, Event

class Server:
    '''
    Part of the PyGaSe backend that handles connections to clients.

    ### Arguments
     - **game_state_store** *GameStateStore*: part of the backend that provides the **GameState**
    
    ### Attributes
     - **connections** *dict*: contains each clients address as a key leading to the
       corresponding **ClientConnection** instance
     - **host_client**: address of the host client, if there is any
     - **game_state_store** *GameStateStore*: part of the backend that provides the **GameState**
    
    ### Properties
     - **hostname** *str*: read-only access to the servers hostname
     - **port** *int*: read-only access to the servers port number
    '''
    def __init__(self, game_state_store:GameStateStore):
        self.connections = {}
        self.host_client = None
        self.game_state_store = game_state_store
        self._universal_event_handler = UniversalEventHandler()
        self._hostname = None
        self._port = None

    def run(self, port:int=0, hostname:str='localhost', event_wire=None):
        '''
        Starts the server under specified address. (Can also be called as a coroutine.)

        ### Arguments
         - **port** *int*: port number the server will be bound to, default will be an available
           port chosen by the computers network controller
         - **hostname** *str*: hostname or IP address the server will be bound to.
           Defaults to `'localhost'`.
         - **event_wire**: object to which events are to be repeated
           (has to implement a *_push_event* method and is typically a **GameStateMachine**)
        '''
        curio.run(self.run, port, hostname, event_wire)

    @awaitable(run)
    async def run(self, port:int=0, hostname:str='localhost', event_wire=None): #pylint: disable=function-redefined
        await ServerConnection.loop(
            hostname, port, self, event_wire
        )

    def run_in_thread(self, port:int=0, hostname:str='localhost', event_wire=None, daemon=True):
        '''
        Starts the server under specified address and in a seperate thread.

        See **Server.run(port, hostname)**.

        ### Returns
        *threading.Thread*: the thread the server loop runs in
        '''
        thread = threading.Thread(target=self.run, args=(port, hostname, event_wire), daemon=daemon)
        thread.start()
        return thread

    @property
    def hostname(self):
        return 'localhost' if self._hostname == '127.0.0.1' else self._hostname

    @property
    def port(self):
        return self._port

    def shutdown(self):
        '''
        Shuts down the server. (can be restarted via **run**)
        '''
        curio.run(self.shutdown)

    @awaitable(shutdown)
    async def shutdown(self): #pylint: disable=function-redefined
        async with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            await sock.sendto('shut_me_down'.encode('utf-8'), (self._hostname, self._port))

    def dispatch_event(self, event_type:str, handler_args:list=[], target_client='all', retries:int=0, ack_callback=None, **kwargs):
        '''
        Sends an event to one or all clients.

        ### Arguments
         - **event_type** *str*: string that identifies the event and links it to a handler
        
        ### Optional Arguments
         - **handler_args** *list*: list of positional arguments to be passed to the handler function that will be invoked
           by the client
         - **target_client**: either `'all'` for an event broadcast or a clients address
         - **retries** *int*: number of times the event is to be resent, in the case it times out
         - **ack_callback**: function or coroutine to be executed after the event was received,
           will be passed a reference to the client connection
         - **kwargs** *dict*: keyword arguments to be passed to the handler function
        '''
        event = Event(event_type, handler_args, kwargs)
        def get_ack_callback(connection): return lambda: ack_callback(connection)
        if retries > 0:
            def get_timeout_callback(connection):
                return lambda: self.dispatch_event(
                    event_type, handler_args,
                    connection,
                    retries-1, ack_callback,
                    **kwargs
                )
        else:
            def get_timeout_callback(connection): return None
        if target_client == 'all':
            for connection in self.connections.values():
                connection.dispatch_event(
                    event,
                    get_ack_callback(connection),
                    get_timeout_callback(connection),
                    **kwargs
                )
        else:
            self.connections[target_client].dispatch_event(
                event,
                get_ack_callback(self.connections[target_client]),
                get_timeout_callback(self.connections[target_client]),
                **kwargs
            )

    def push_event_handler(self, event_type:str, handler_func):
        '''
        ### Arguments
         - **event_type** *str*: event type to link the handler function to
         - **handler_func**: function or coroutine to be invoked for events of the given type
        '''
        self._universal_event_handler.push_event_handler(event_type, handler_func)
