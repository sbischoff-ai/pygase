# -*- coding: utf-8 -*-

from pygase import aio
import pytest
from freezegun import freeze_time

from helpers import assert_timeout

from pygase.backend import Server, GameStateMachine, GameStateStore
from pygase.client import Client
from pygase.gamestate import GameState, GameStatus


@pytest.mark.integration
class TestIntegration:
    def test_client_server_connection(self):
        server = Server(GameStateStore())
        client = Client()

        async def test_task():
            await aio.spawn(server.run)
            await assert_timeout(3, lambda: server.port is not None)
            await aio.spawn(client.connect, server.port)
            await assert_timeout(3, lambda: server.connections != {})
            assert client.connection.remote_address == (server.hostname, server.port)
            await aio.sleep(0)
            await server.shutdown()
            return True

        assert aio.run(test_task)

    def test_connect_disconnect(self):
        init_gamestate = GameState(counter=0, test="foobar")
        state_store = GameStateStore(init_gamestate)
        state_machine = GameStateMachine(state_store)

        def test_update(game_state, dt):
            counter = game_state.counter + 1
            test = "foobar" if counter % 2 == 0 else "barfoo"
            return {"test": test, "counter": counter}

        state_machine.time_step = test_update
        server = Server(state_store)
        client = Client()

        async def test_task(client_shutdown):
            server_task = await aio.spawn(server.run)
            await assert_timeout(3, lambda: server._port is not None)
            client_task = await aio.spawn(client.connect, server.port, server.hostname)
            await assert_timeout(3, lambda: client.connection is not None)
            state_machine_task = await aio.spawn(state_machine.run_game_loop)
            await assert_timeout(3, lambda: state_store.get_game_state().game_status == GameStatus.ACTIVE)
            await state_machine.stop()
            await state_machine_task.join()
            await client.disconnect(shutdown_server=client_shutdown)
            await client_task.join()
            if not client_shutdown:
                await server.shutdown()
            await server_task.join()
            return True

        assert aio.run(test_task, True, with_monitor=True)
        assert aio.run(test_task, False, with_monitor=True)
