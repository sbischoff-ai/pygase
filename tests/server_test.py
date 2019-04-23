# -*- coding: utf-8 -*-

import curio

from helpers import assert_timeout

from pygase.server import Server
from pygase.connection import ClientPackage
from pygase.gamestate import GameStateStore
from pygase.event import UniversalEventHandler

class TestServer:

    def test_instantiation(self):
        server = Server(GameStateStore())
        assert server.game_state_store.__class__ == GameStateStore
        assert server._universal_event_handler.__class__ == UniversalEventHandler

    def test_run_async(self):
        server = Server(GameStateStore())
        async def test_task():
            await curio.spawn(server.run, 1234)
            await assert_timeout(1, lambda: server.hostname == 'localhost')
            assert server._port == 1234
            await server.shutdown()
            return True
        assert curio.run(test_task)
