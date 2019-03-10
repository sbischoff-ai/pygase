# -*- coding: utf-8 -*-

from pygase.network_protocol import Package, Connection, BUFFER_SIZE
from curio import socket

class Client:

    def __init__(self, remote_hostname, remote_port):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connection = Connection((remote_hostname, remote_port))

    async def _send_and_recv(self, package: Package):
        # Send package to server ...
        await self._socket.sendto(package.to_datagram(), self.connection.remote_address)
        # ... and get response if possible, otherwise create ServerError package
        try:
            return Package.from_datagram(await self._socket.recv(BUFFER_SIZE))
        except socket.timeout:
            print('timeout') #return pygase.shared.timeout_error('Request timed out.')
        except ConnectionResetError:
            print('server not found') #return pygase.shared.timeout_error('Server not found.')
