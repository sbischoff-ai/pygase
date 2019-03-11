# -*- coding: utf-8 -*-

import threading

import curio
from curio import socket

from pygase.network_protocol import Package, Connection

class Client:

    def __init__(self):
        self.connection = None
        self._event_queue = curio.UniversalQueue()
        self._connection_thread = None

    def connect(self, port:int, hostname:str='localhost'):
        self.connection = Connection((hostname, port))
        self._connection_thread = threading.Thread(target=curio.run, args=(self._client_task,))
        self._connection_thread.start()

    async def _client_task(self):
        async with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            send_loop_task = await curio.spawn(self.connection.send_loop, sock, self._event_queue)
            recv_loop_task = await curio.spawn(self._recv_loop, sock)
            # handle events
            while True:
                event = await self._event_queue.get()
                if event == 'shutdown':
                    await sock.sendto('shutdown'.encode('utf-8'), self.connection.remote_address)
                    break
            await recv_loop_task.cancel()
            await send_loop_task.cancel()

    async def _recv_loop(self, sock):
        while True:
            data = await sock.recv(Package.max_size)
            package = Package.from_datagram(data)
            self.connection.recv(package)
