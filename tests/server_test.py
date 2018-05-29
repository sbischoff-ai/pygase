# -*- coding: utf-8 -*-

import socket
import PyGaSe.server
import PyGaSe.shared

class TestServer:

    server_address = ('localhost', 9998)
    server = PyGaSe.server.Server(
        ip_address=server_address[0],
        port=server_address[1],
        game_loop_class=PyGaSe.server.GameLoop,
        game_state=PyGaSe.shared.GameState()
    )
    mock_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    mock_client_socket.settimeout(1.0)

    def mock_client_request(self, datagram: bytes):
        self.mock_client_socket.sendto(datagram, self.server_address)

    def mock_client_recv(self, buffer_size=1024):
        return self.mock_client_socket.recv(buffer_size)

    def test_server_instantiation(self):
        assert self.server.game_state == PyGaSe.shared.GameState()
        assert self.server.RequestHandlerClass.__name__ == 'ServerRequestHandler'

    def test_server_request_handler(self):
        self.server.server_activate()
        self.mock_client_request(
            PyGaSe.shared.UDPPackage(PyGaSe.shared.PackageType.GetGameStateRequest).to_datagram()
        )
        self.server.handle_request()
        response = PyGaSe.shared.UDPPackage.from_datagram(self.mock_client_recv())
        assert response.header.package_type == PyGaSe.shared.PackageType.ServerResponse
        self.mock_client_request(bytes('Not a proper package', 'utf-8'))
        self.server.handle_request()
        response = PyGaSe.shared.UDPPackage.from_datagram(self.mock_client_recv())
        assert response.header.package_type == PyGaSe.shared.PackageType.ServerError and \
               response.body.error_type == PyGaSe.shared.ErrorType.UnpackError
        self.mock_client_request(
            PyGaSe.shared.UDPPackage(PyGaSe.shared.PackageType.ServerResponse).to_datagram()
        )
        self.server.handle_request()
        response = PyGaSe.shared.UDPPackage.from_datagram(self.mock_client_recv())
        assert response.header.package_type == PyGaSe.shared.PackageType.ServerError
        self.server.server_close()
