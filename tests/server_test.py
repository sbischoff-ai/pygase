# -*- coding: utf-8 -*-

import socket
import pygase.server
import pygase.shared

class TestServer:

    server_address = ('localhost', 9998)
    server = pygase.server.Server(
        ip_address=server_address[0],
        port=server_address[1],
        game_loop_class=pygase.server.GameLoop,
        game_state=pygase.shared.GameState()
    )
    mock_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    mock_client_socket.settimeout(1.0)

    def mock_client_request(self, datagram: bytes):
        self.mock_client_socket.sendto(datagram, self.server_address)

    def mock_client_recv(self, buffer_size=1024):
        return self.mock_client_socket.recv(buffer_size)

    def test_server_instantiation(self):
        assert self.server.game_state == pygase.shared.GameState()
        assert self.server.RequestHandlerClass.__name__ == 'ServerRequestHandler'

    def test_server_request_handler(self):
        self.server.server_activate()
        self.mock_client_request(
            pygase.shared.UDPPackage(pygase.shared.PackageType.GetGameStateRequest).to_datagram()
        )
        self.server.handle_request()
        response = pygase.shared.UDPPackage.from_datagram(self.mock_client_recv())
        assert response.header.package_type == pygase.shared.PackageType.ServerResponse
        self.mock_client_request(bytes('Not a proper package', 'utf-8'))
        self.server.handle_request()
        response = pygase.shared.UDPPackage.from_datagram(self.mock_client_recv())
        assert response.header.package_type == pygase.shared.PackageType.ServerError and \
               response.body.error_type == pygase.shared.ErrorType.UnpackError
        self.mock_client_request(
            pygase.shared.UDPPackage(pygase.shared.PackageType.ServerResponse).to_datagram()
        )
        self.server.handle_request()
        response = pygase.shared.UDPPackage.from_datagram(self.mock_client_recv())
        assert response.header.package_type == pygase.shared.PackageType.ServerError
        self.server.server_close()
