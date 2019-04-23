import sys
from pygase import Server, GameState, GameStateStore, GameStateMachine

initial_game_state = GameState(
    players={}, # dict with `player_id: player_dict` entries
    chaser_id=None, # id of player who is chaser
    protection=None, # wether protection from the chaser is active
    countdown=0.0 # countdown until protection is lifted
)
game_state_store = GameStateStore(initial_game_state)
game_state_machine = GameStateMachine(game_state_store)

def on_join(player_name, game_state, dt):
    print('Player', player_name, 'joined.')
    # count up for player ids, starting with 1
    player_id = max(game_state.players.keys()) + 1 if game_state.players else 1
    return {
        'players': {
            player_id: {
                'name': player_name,
                'position': (0, 0)
            }
        },
        'chaser_id': player_id if game_state.chaser_id is None else game_state.chaser_id
    }

def on_move(player_id, new_position, game_state, dt):
    return {
        'players': {
            player_id: {
                'position': new_position
            }
        }
    }

def time_step(game_state, dt):
    # Before a player joins, updating the game state is unnecessary.
    if game_state.chaser_id is None:
        return {}
    # If protection mode is on, all players are safe from the chaser.
    if game_state.protection:
        new_countdown = game_state.countdown - dt
        return {
            'countdown': new_countdown,
            'protection': True if new_countdown >= 0.0 else False
        }
    # Check if chaser got someone
    chaser = game_state.players[game_state.chaser_id]
    for player_id, player in game_state.players.items():
        if not player_id == game_state.chaser_id:
            # Calculate their distance to the chaser.
            dx = player['position'][0] - chaser['position'][0]
            dy = player['position'][1] - chaser['position'][1]
            distance_squared = dx*dx + dy*dy
            # When the chaser touches another player, that player becomes
            # chaser and the protection countdown starts.
            if distance_squared < 15:
                print(player['name'], 'has been caught')
                return {
                    'chaser_id': player_id,
                    'protection': True,
                    'countdown': 5.0
                }
    return {}
        
game_state_machine.time_step = time_step
game_state_machine.push_event_handler(event_type='JOIN', handler_func=on_join)
game_state_machine.push_event_handler(event_type='MOVE', handler_func=on_move)

server = Server(game_state_store)

game_state_machine.run_game_loop_in_thread()
server.run(hostname='localhost', port=8080, event_wire=game_state_machine)
