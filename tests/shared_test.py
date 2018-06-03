# -*- coding: utf-8 -*-

import pytest
import pygase.shared

class TestGameState:

    def test_game_state_instantiation(self):
        game_state = pygase.shared.GameState()
        assert game_state.time_order == 0
        assert game_state.game_status == pygase.shared.GameStatus.Paused
        paused_game_state = pygase.shared.GameState(game_status=pygase.shared.GameStatus.Active)
        assert game_state.game_status != paused_game_state.game_status
        paused_game_state.game_status = pygase.shared.GameStatus.Paused
        assert game_state == paused_game_state

    def test_game_state_bytepacking(self):
        game_state = pygase.shared.GameState()
        game_state.test_pos = 2.5
        bytepack = game_state.to_bytes()
        unpacked_game_state = pygase.shared.GameState.from_bytes(bytepack)
        assert game_state == unpacked_game_state
        with pytest.raises(TypeError) as exception:
            pygase.shared.GameState.from_bytes(
                'This is not a pygase.shared.GameState'.encode('utf-8')
            )
            assert str(exception.value) == 'Bytes could no be parsed into GameState.'

    def test_update_arithmetic(self):
        game_state = pygase.shared.GameState(
            time_order=0,
            game_status=pygase.shared.GameStatus.Paused
        )
        update = pygase.shared.GameStateUpdate(
            time_order=0,
            test=0
        )
        game_state += update
        assert not hasattr(game_state, 'test') and game_state.time_order == 0
        update.time_order = 1
        game_state += update
        assert game_state.test == 0 and game_state.time_order == 1
        update.time_order = 2
        update.test = pygase.shared.TO_DELETE
        game_state += update
        assert not hasattr(game_state, 'test') and game_state.time_order == 2
        update.time_order = 1
        update.test = 2
        game_state += update
        assert not hasattr(game_state, 'test') and game_state.time_order == 2
        game_state.test = 0
        update += pygase.shared.GameStateUpdate(
            time_order=3,
            test=pygase.shared.TO_DELETE
        )
        assert update.time_order == 3 and update.test == pygase.shared.TO_DELETE
        assert hasattr(game_state, 'test') and game_state.time_order == 2
        game_state += update
        assert not hasattr(game_state, 'test') and game_state.time_order == 3
        update += pygase.shared.GameStateUpdate(
            time_order=4,
            test='test'
        )
        assert update.test == 'test' and update > game_state
        game_state += pygase.shared.GameStateUpdate(
            time_order=3,
            test={1: pygase.shared.TO_DELETE}
        ) + pygase.shared.GameStateUpdate(
            time_order=5,
            test={1: 'test1', 2: 'test2'}
        ) + update
        assert game_state.time_order == 5 and game_state.test[1] == 'test1'
