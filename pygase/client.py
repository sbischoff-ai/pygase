# -*- coding: utf-8 -*-

#import threading

import curio
from curio import socket

from pygase.network_protocol import Package, Connection

class Client:

    def __init__(self):
        self.connection = None
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #self._connection_thread = None

    def connect(self, remote_hostname, remote_port):
        self.connection = Connection((remote_hostname, remote_port))
        curio.run(self._client_task)

    async def _client_task(self):
        send_loop_task = await curio.spawn(self.connection.send_loop, self._socket)
        recv_loop_task = await curio.spawn(self._recv_loop)
        await curio.sleep(6) # For testing purposes, the client only runs 1 second
        async with self._socket:
            await recv_loop_task.cancel()
            await send_loop_task.join()
            await self._socket.sendto('shutdown'.encode('utf-8'), self.connection.remote_address)

    async def _recv_loop(self):
        while True:
            data = await self._socket.recv(Package.max_size)
            package = Package.from_datagram(data)
            self.connection.recv(package)

