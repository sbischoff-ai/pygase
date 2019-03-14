# -*- coding: utf-8 -*-

import curio

from pygase.network_protocol import ServerConnection
from pygase.event import UniversalEventHandler

class Server:
    
    def __init__(self):
        self.connections = {}

    def run(self, port:int=0, hostname:str='localhost'):
        curio.run(ServerConnection.loop, hostname, port, self.connections)
