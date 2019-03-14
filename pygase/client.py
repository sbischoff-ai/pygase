# -*- coding: utf-8 -*-

import threading

import curio

from pygase.network_protocol import ClientConnection
from pygase.event import UniversalEventHandler

class Client:

    def __init__(self):
        self.connection = None
        self._connection_thread = None

    def connect(self, port:int, hostname:str='localhost'):
        self.connection = ClientConnection((hostname, port))
        self._connection_thread = threading.Thread(
            target=curio.run,
            args=(self.connection.loop,)
        )
        self._connection_thread.start()
