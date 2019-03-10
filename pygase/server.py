# -*- coding: utf-8 -*-

import curio
from curio import socket

from pygase.network_protocol import Package, Connection, ProtocolIDMismatchError

class Server:
    
    def __init__(self):
        self.connections = {}
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self, hostname='localhost', port=0):
        self._socket.bind((hostname, port))
        curio.run(self._server_task)
    
    async def _server_task(self):
        send_loop_tasks = []
        recv_loop_task = await curio.spawn(self._recv_loop, send_loop_tasks)
        async with self._socket:
            await recv_loop_task.join()
            for task in send_loop_tasks:
                await task.cancel()

    async def _recv_loop(self, send_loop_tasks: list):
        while True:
            data, client_address = await self._socket.recvfrom(Package.max_size)
            try:
                package = Package.from_datagram(data)
                # create new connection if client is unknown
                if not client_address in self.connections:
                    new_connection = Connection(client_address)
                    new_connection.set_status('Connected')
                    send_loop_tasks.append(await curio.spawn(new_connection.send_loop, self._socket))
                    self.connections[client_address] = new_connection
                self.connections[client_address].recv(package)
            except ProtocolIDMismatchError:
                # ignore all non-Pygase packages
                pass
            # this is a rudimentary shutdown switch
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
