# -*- coding: utf-8 -*-

import curio
from freezegun import freeze_time
import pytest

from pygase.gamestate import GameState, GameStateUpdate, GameStatus, TO_DELETE, \
    GameStateStore, GameStateMachine

class TestGameState:

    def test_bytepacking(self):
        game_state = GameState()
        bytepack = game_state.to_bytes()
        unpacked_game_state = GameState.from_bytes(bytepack)
        assert game_state == unpacked_game_state

    def test_game_state_instantiation(self):
        game_state = GameState()
        assert game_state.time_order == 0
        assert game_state.game_status == GameStatus.get('Paused')
        paused_game_state = GameState(game_status=GameStatus.get('Active'))
        assert game_state.game_status != paused_game_state.game_status
        paused_game_state.game_status = GameStatus.get('Paused')
        assert game_state == paused_game_state

class TestGameStateUpdate:

    def test_bytepacking(self):
        update = GameStateUpdate(5)
        bytepack = update.to_bytes()
        unpacked_update = GameStateUpdate.from_bytes(bytepack)
        assert update == unpacked_update

    def test_update_arithmetic(self):
        game_state = GameState(
            time_order=0,
            game_status=GameStatus.get('Paused')
        )
        update = GameStateUpdate(
            time_order=0,
            test=0
        )
        game_state += update
        assert not hasattr(game_state, 'test') and game_state.time_order == 0
        update.time_order = 1
        game_state += update
        assert game_state.test == 0 and game_state.time_order == 1
        update.time_order = 2
        update.test = TO_DELETE
        game_state += update
        assert not hasattr(game_state, 'test') and game_state.time_order == 2
        update.time_order = 1
        update.test = 2
        game_state += update
        assert not hasattr(game_state, 'test') and game_state.time_order == 2
        game_state.test = 0
        update += GameStateUpdate(
            time_order=3,
            test=TO_DELETE
        )
        assert update.time_order == 3 and update.test == TO_DELETE
        assert hasattr(game_state, 'test') and game_state.time_order == 2
        game_state += update
        assert not hasattr(game_state, 'test') and game_state.time_order == 3
        update += GameStateUpdate(
            time_order=4,
            test='test'
        )
        assert update.test == 'test' and update > game_state
        game_state += GameStateUpdate(
            time_order=3,
            test={1: TO_DELETE}
        ) + GameStateUpdate(
            time_order=5,
            test={1: 'test1', 2: 'test2'}
        ) + update
        assert game_state.time_order == 5 and game_state.test[1] == 'test1'

class TestGameStateStore:

    def test_instantiation(self):
        store = GameStateStore()
        assert store._game_state == GameState()
        assert store._game_state_update_cache == [GameStateUpdate(0)]

    def test_push_update(self):
        store = GameStateStore()
        store.push_update(GameStateUpdate(1, test='foobar'))
        assert len(store._game_state_update_cache) == 2
        assert store.get_game_state().time_order == 1
        assert store.get_game_state().test == 'foobar'

    def test_safe_concurrent_cache_access(self):
        store = GameStateStore()
        store.push_update(GameStateUpdate(2))
        counter = 0
        for update in store.get_update_cache():
            counter += 1
            if update.time_order == 2:
                store.push_update(GameStateUpdate(3))
        assert counter == 2
        counter = 0
        for update in store.get_update_cache():
            counter += 1
            if update.time_order == 0:
                del store._game_state_update_cache[2]
        assert counter == 3
        assert len(store.get_update_cache()) == 2

class TestGameStateMachine:

    def test_instantiation(self):
        state_machine = GameStateMachine(GameStateStore())
        assert state_machine.game_time == 0
        assert state_machine._game_state_store._game_state_update_cache == [GameStateUpdate(0)]

    def test_abstractness(self):
        state_machine = GameStateMachine(GameStateStore())
        with pytest.raises(NotImplementedError):
            state_machine.time_step(GameState(), 0.1)

    def test_game_loop(self):
        class MyStateMachine(GameStateMachine):
            def time_step(self, game_state, dt):
                test = game_state.test + 1
                return {'test': test}
        store = GameStateStore(GameState(0, test=0))
        state_machine = MyStateMachine(store)
        async def test_task():
            with freeze_time() as frozen_time:
                game_loop = await curio.spawn(state_machine.run_game_loop, 1)
                for _ in range(10):
                    frozen_time.tick()
                    await curio.sleep(0)
                await state_machine.stop()
                await game_loop.join()
            return True
        assert curio.run(test_task)
        assert store.get_game_state().time_order == 12
        assert store.get_game_state().test == 10
        assert state_machine.game_time == 10
        assert store.get_game_state().game_status == GameStatus.get('Paused')
