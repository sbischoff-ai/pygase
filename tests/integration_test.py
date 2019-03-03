# -*- coding: utf-8 -*-

import time
import pygase.client
import pygase.server
import pygase.shared

class TestIntegration:

    server_address = ('localhost', 3456)
    server = pygase.server.Server(
            server_address[0],
            server_address[1],
            pygase.server.GameLoop,
            pygase.shared.GameState()
        )

    def test_client_server_connection(self):
        connection = pygase.client.Connection(self.server_address)
        assert connection.is_waiting()
        self.server.start()
        time.sleep(pygase.client.CONNECTION_TIMEOUT)
        assert connection.is_connected()
        assert not connection.game_state.is_paused()
        connection.post_client_activity(pygase.shared.toggle_pause_activity(connection.game_state))
        assert len(connection._polled_client_activities) == 1
        time.sleep(pygase.client.REQUEST_TIMEOUT)
        assert connection.game_state.is_paused()
        self.server.shutdown()
        time.sleep(1.5*pygase.client.REQUEST_TIMEOUT)
        assert connection.is_waiting()
        time.sleep(pygase.client.CONNECTION_TIMEOUT)
        assert connection.connection_status == pygase.client.ConnectionStatus.Disconnected

    def test_join_server(self):
        connection = pygase.client.Connection(self.server_address)
        self.server.start()
        connection.post_client_activity(pygase.shared.join_server_activity('Bob'))
        assert len(connection._polled_client_activities) == 1
        assert connection._polled_client_activities[0].activity_type == pygase.shared.ActivityType.JoinServer
        time.sleep(1.5*pygase.client.REQUEST_TIMEOUT)
        assert connection.game_state.players[0]['name'] == 'Bob'
        self.server.shutdown()