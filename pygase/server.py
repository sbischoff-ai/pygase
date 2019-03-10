# -*- coding: utf-8 -*-

import curio
from curio import socket, time

from pygase.network_protocol import Package, Connection, ProtocolIDMismatchError, BUFFER_SIZE

class Server:
    
    def __init__(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connections = {}

    def run(self, hostname='localhost', port=0):
        self._socket.bind((hostname, port))
        curio.run(self._serve)
    
    async def _serve(self):
        while True:
            async with self._socket:
                data, client_address = await self._socket.recvfrom(BUFFER_SIZE)
                try:
                    package = Package.from_datagram(data)                
                    if not client_address in self.connections:
                        self.connections[client_address] = Connection(client_address)
                        self.connections[client_address].set_status('Good')
                    connection = self.connections[client_address]
                    connection.update(package)
                    connection.local_sequence += 1
                    response = Package(connection.local_sequence, connection.remote_sequence, connection.ack_bitfield)
                    await self._socket.sendto(response.to_datagram(), client_address)
                except ProtocolIDMismatchError:
                    pass
                try:
                    if data.decode('utf-8') == 'shutdown':
                        break
                except UnicodeDecodeError:
                    pass

    @property
    def hostname(self):
        return self._socket.getsockname()[0]

    @property
    def port(self):
        return self._socket.getsockname()[1]
