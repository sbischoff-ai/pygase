import sys
import pygase.shared, pygase.server
import chase.shared_stuff

# Create your server-side game state object with initial data.
SHARED_GAME_STATE = pygase.shared.GameState()
SHARED_GAME_STATE.chaser = None
SHARED_GAME_STATE.protection = False
SHARED_GAME_STATE.countdown = 0.0

# Implement your own server-side game loop.
class ChaseGameLoop(pygase.server.GameLoop):

    # Override the on_join method to define your initial player data.
    def on_join(self, player_id, update):
        # Just assign any attribute to the GameStateUpdate object that
        # you want to be overwritten or added the shared game state.
        update.players[player_id]['position'] = (0, 0)
        # The first player to join will be the first chaser
        if self.server.game_state.chaser is None:
            self.server.game_state.chaser = player_id

    # Override the handle_activity method to handle your custom client
    # activities within the server-side game loop.
    def handle_activity(self, activity, update, dt):
        if activity.activity_type == pygase.shared.ActivityType.MovePlayer:
            player_id = activity.activity_data['player_id']
            new_position = activity.activity_data['new_position']
            # The update object works the same way as in on_join.
            update.players = {
                player_id: {'position': new_position}
            }
    
    # Override the update_game_state method to implement your own
    # game logic.
    def update_game_state(self, update, dt):
        # Before a player joins, updating the game state is unnecessary.
        if self.server.game_state.chaser is None:
            return
        # If protection mode is on, all players are safe from the chaser.
        if self.server.game_state.protection:
            update.countdown = self.server.game_state.countdown - dt
            # When the countdown is over, protection mode is switched off.
            if update.countdown <= 0.0:
                update.protection = False
            return
        chaser = self.server.game_state.players[self.server.game_state.chaser]
        # Iterate through all players.
        for player_id, player in self.server.game_state.players.items():
            if not player_id == self.server.game_state.chaser:
                # Calculate their distance to the chaser.
                dx = player['position'][0] - chaser['position'][0]
                dy = player['position'][1] - chaser['position'][1]
                distance_squared = dx*dx + dy*dy
                # When the chaser touches another player, that player becomes
                # chaser and the protection countdown starts.
                if distance_squared < 15:
                    update.chaser = player_id
                    update.protection = True
                    update.countdown = 5.0

# Finally create the server object. If you want to test this online, you
# will have to put in your ethernet adapter's IP address and deal with
# port-forwarding to your external IP address.
SERVER = pygase.server.Server(
    ip_address='127.0.0.1',
    port=8080,
    game_loop_class=ChaseGameLoop,
    game_state=SHARED_GAME_STATE
)

# Start the server and keep it running until the user writes the line 
# 'shutdown' into the servers Python terminal.
SERVER.start()
while not sys.stdin.readline().__contains__('shutdown'):
    pass
SERVER.shutdown()