# -*- coding: utf-8 -*-

import time
import socketserver
import pygase.client
import pygase.shared

class TestClient:

    server_address = ('localhost', 2345)

    def test_connection_instantiation(self):
        connection = pygase.client.Connection(self.server_address)
        connection_start = time.time()
        assert connection.game_state == pygase.shared.GameState()
        assert connection._polled_client_activities == []
        while time.time() - connection_start < pygase.client.CONNECTION_TIMEOUT:
            assert connection.is_waiting() and not connection.is_connected()
            assert connection._update_cycle_thread.is_alive()
        time.sleep(0.3) # some tolerance
        assert not connection.is_waiting() and not connection.is_connected()
        assert not connection._update_cycle_thread.is_alive()
