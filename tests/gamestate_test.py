# -*- coding: utf-8 -*-

from pygase.gamestate import GameState, GameStateUpdate, GameStatus, TO_DELETE


def test_game_status_enum_values():
    assert GameStatus.PAUSED.value == 0
    assert GameStatus.ACTIVE.value == 1


class TestGameState:
    def test_bytepacking(self):
        game_state = GameState(time_order=3, game_status=GameStatus.ACTIVE, foo="bar")
        bytepack = game_state.to_bytes()
        unpacked_game_state = GameState.from_bytes(bytepack)
        assert game_state == unpacked_game_state

    def test_game_state_instantiation(self):
        game_state = GameState()
        assert game_state.time_order == 0
        assert game_state.game_status == GameStatus.PAUSED
        paused_game_state = GameState(game_status=GameStatus.ACTIVE)
        assert game_state.game_status != paused_game_state.game_status
        paused_game_state.game_status = GameStatus.PAUSED
        assert game_state == paused_game_state

    def test_custom_state_is_kept_in_data_dict(self):
        game_state = GameState(player_hp=100)
        assert game_state.data == {"player_hp": 100}
        assert game_state.player_hp == 100
        game_state.player_hp = 90
        assert game_state.data["player_hp"] == 90

    def test_structural_fields_are_not_overwritten_by_data(self):
        game_state = GameState(time_order=4, game_status=GameStatus.ACTIVE, **{"data": "ignored"})
        assert game_state.time_order == 4
        assert game_state.game_status == GameStatus.ACTIVE
        assert game_state.data == {"data": "ignored"}


class TestGameStateUpdate:
    def test_bytepacking(self):
        update = GameStateUpdate(5, game_status=GameStatus.ACTIVE, test="value")
        bytepack = update.to_bytes()
        unpacked_update = GameStateUpdate.from_bytes(bytepack)
        assert update == unpacked_update

    def test_update_arithmetic(self):
        game_state = GameState(time_order=0, game_status=GameStatus.PAUSED)
        update = GameStateUpdate(time_order=0, test=0)
        game_state += update
        assert not hasattr(game_state, "test") and game_state.time_order == 0
        update.time_order = 1
        game_state += update
        assert game_state.test == 0 and game_state.time_order == 1
        update.time_order = 2
        update.test = TO_DELETE
        game_state += update
        assert not hasattr(game_state, "test") and game_state.time_order == 2
        update.time_order = 1
        update.test = 2
        game_state += update
        assert not hasattr(game_state, "test") and game_state.time_order == 2
        game_state.test = 0
        update += GameStateUpdate(time_order=3, test=TO_DELETE)
        assert update.time_order == 3 and update.test == TO_DELETE
        assert hasattr(game_state, "test") and game_state.time_order == 2
        game_state += update
        assert not hasattr(game_state, "test") and game_state.time_order == 3
        update += GameStateUpdate(time_order=4, test="test")
        assert update.test == "test" and update > game_state
        game_state += (
            GameStateUpdate(time_order=3, test={1: TO_DELETE})
            + GameStateUpdate(time_order=5, test={1: "test1", 2: "test2"})
            + update
        )
        assert game_state.time_order == 5 and game_state.test[1] == "test1"

    def test_update_can_set_game_status(self):
        game_state = GameState(time_order=0, game_status=GameStatus.PAUSED)
        game_state += GameStateUpdate(time_order=1, game_status=GameStatus.ACTIVE)
        assert game_state.game_status == GameStatus.ACTIVE
        assert game_state.time_order == 1

    def test_structural_time_order_cannot_be_overwritten_by_payload(self):
        update = GameStateUpdate.from_dict({"time_order": 3, "time_order_payload": 1})
        game_state = GameState(time_order=0)
        game_state += update
        assert game_state.time_order == 3
        assert game_state.time_order_payload == 1
