# -*- coding: utf-8 -*-

import pytest
import PyGaSe.shared

class TestGameState:

    game_state = PyGaSe.shared.GameState()

    def test_game_state_instantiation(self):
        assert self.game_state.game_status == PyGaSe.shared.GameStatus.Paused
        paused_game_state = PyGaSe.shared.GameState(game_status=PyGaSe.shared.GameStatus.Active)
        assert self.game_state.game_status != paused_game_state.game_status
        paused_game_state.game_status = PyGaSe.shared.GameStatus.Paused
        assert self.game_state == paused_game_state

    def test_game_state_bytepacking(self):
        bytepack = self.game_state.to_bytes()
        unpacked_game_state = PyGaSe.shared.GameState.from_bytes(bytepack)
        assert self.game_state == unpacked_game_state
        with pytest.raises(TypeError) as exception:
            PyGaSe.shared.GameState.from_bytes('This is not a PyGaSe.shared.GameState'.encode('utf-8'))
            assert str(exception.value) == 'Bytes could no be parsed into GameState.'
