# -*- coding: utf-8 -*-

import threading

from pygase.server import Server
from pygase.connection import ClientPackage
from pygase.gamestate import GameStateStore
from pygase.event import UniversalEventHandler

class TestServer:

    def test_instantiation(self):
        server = Server()
        assert server.game_state_store.__class__ == GameStateStore
        assert server._universal_event_handler.__class__ == UniversalEventHandler

'''
THREADING PROBLEM WITH PYTEST?
    def test_run_in_thread(self):
        server = Server()
        thread = server.run_in_thread()
        assert thread.is_alive()
        server.shutdown()
        thread.join()
        assert not thread.is_alive()
'''
