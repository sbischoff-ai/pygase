# PyGaSe
**Py**thon**Ga**me**Se**rver

A Python package that contains a versatile high-performance UDP-based game server, client and network protocol with a simple API.

## Usage

This example implements an online game of chase, in which players can move around,
while one of them is the chaser who has to catch another player, thereby passing
the role of chaser to that player.

### Server

```Python
import sys
import pygase.shared
import pygase.server

# Create your server-side game state object with initial data.
SHARED_GAME_STATE = pygase.shared.GameState()
SHARED_GAME_STATE.chaser = None

# Define your own client activities.
pygase.shared.ActivityType.add_type('MovePlayer')
# (Ideally you do this in an imported module that is shared by both
# your client and your server implementation.)

# Implement your own server-side game loop.
class MyGameLoop(pygase.server.GameLoop):

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
    def handle_activity(self, activity, update):
        if activity.activity_type == pygase.shared.ActivityType.MovePlayer:
            player_id = activity.activity_data['player_id']
            new_position = activity.activity_data['new_position']
            # The update object works the same way as in on_join.
            update.players[player_id]['position'] = new_position
    
    # Override the update_game_state method to implement your own
    # game logic.
    def update_game_state(self, update, dt):
        TODO

# Finally create the server object. If you want to test this online, you
# will have to put in your ethernet adapter's IP address and deal with
# port-forwarding to your external IP address.
SERVER = pygase.server.Server(
    ip_address='127.0.0.1',
    port=8080,
    game_loop_class=MyGameLoop,
    game_state=SHARED_GAME_STATE
)

# Start the server and keep it running until the user writes the line 
# 'shutdown' into the servers Python terminal.
SERVER.start()
while not sys.stdin.readline() == 'shutdown':
    pass
SERVER.shutdown()
```

### Client

```Python
import pygase.shared
import pygase.client

TODO
```

TODO
