# -*- coding: utf-8 -*-

import curio
from curio import socket

from pygase.network_protocol import Package, Connection, ProtocolIDMismatchError

class Server:
    
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connections = {}
        self._is_running = False

    def run(self, hostname='localhost', port=0):
        self.socket.bind((hostname, port))
        self._is_running = True
        curio.run(self._serve)
    
    async def _serve(self):
        while self._is_running:
            data, client_address = await self.socket.recvfrom(1024)
            try:
                package = Package.from_datagram(data)                
                if not client_address in self.connections:
                    self.connections[client_address] = Connection(client_address)
                connection = self.connections[client_address]
                connection.update(package)
                connection.local_sequence += 1
                response = Package(connection.local_sequence, connection.remote_sequence, connection.ack_bitfield)
                await self.socket.sendto(response.to_datagram(), client_address)
            except ProtocolIDMismatchError:
                pass
            try:
                if data.decode('utf-8') == 'shutdown':
                    await self.shutdown()
            except UnicodeDecodeError:
                pass

    @property
    def hostname(self):
        return self.socket.getsockname()[0]

    @property
    def port(self):
        return self.socket.getsockname()[1]

    @property
    def is_running(self):
        return self._is_running

    async def shutdown(self):
        self._is_running = False
        await self.socket.close()
