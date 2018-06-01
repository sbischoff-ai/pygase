# PyGaSe
**Py**thon**Ga**me**Se**rver

A Python package that contains a versatile high-performance UDP-based game server, client and network protocol with a simple API.

## Usage Example

This example implements an online game of chase, in which players can move around,
while one of them is the chaser who has to catch another player, thereby passing
the role of chaser to that player. For a complete API documentation check out the
GitHub page.

### Shared

```Python
# my_games_shared_stuff.py

import pygase.shared

# Define your own client activities.
pygase.shared.ActivityType.add_type('MovePlayer')
```

### Server

```Python
import sys
import pygase.shared, pygase.server
import my_games_shared_stuff

# Create your server-side game state object with initial data.
SHARED_GAME_STATE = pygase.shared.GameState()
SHARED_GAME_STATE.chaser = None
SHARED_GAME_STATE.protection = False
SHARED_GAME_STATE.countdown = 0.0

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
                if distance_squared < 10:
                    update.chaser = player_id
                    update.protection = True
                    update.countdown = 5.0

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
while not sys.stdin.readline().__contains__('shutdown'):
    pass
SERVER.shutdown()
```

### Client

```Python
import pygame
from pygame.locals import *
import pygase.shared, pygase.client
import my_games_shared_stuff

# Establish a connection with the running server.
# For online gaming you have to use another IP of course.
CONNECTION = pygase.client.Connection(('127.0.0.1', 8080))
# Join a new player to the server.
PLAYER_NAME = input('Player name: ')
CONNECTION.post_client_activity(
    pygase.shared.join_server_activity(PLAYER_NAME)
)
# Get the player's ID.
PLAYER_ID = None
while not PLAYER_ID:
    for player_id, player in CONNECTION.game_state.players.items():
        if player['name'] == PLAYER_NAME:
            PLAYER_ID = player_id

# Initialize a pygame screen
pygame.init()
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 420
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Little function to draw players as colored circles
# Green: Yourself
# Blue: Others
# Red: The chaser
def draw_player(position, is_chaser, is_self):
    if is_self:
        color = (50, 255, 50)
    color = (255, 50, 50) if is_chaser else (50, 50, 255)
    pygame.draw.circle(SCREEN, color, position, 5)

# Keep track of pressed keys.
KEYS_PRESSED = set()

# Keep track of time.
CLOCK = pygame.time.Clock()

# The client's game loop
SHUTDOWN = False
while not SHUTDOWN:
    dt = CLOCK.tick(60)
    # Clear the screen and draw all players
    SCREEN.fill((0, 0, 0))
    for player_id, player in CONNECTION.game_state.players.items():
        is_chaser = player_id == CONNECTION.game_state.chaser
        is_self = player_id == PLAYER_ID
        draw_player(player['position'], is_chaser, is_self)
    # Handle events
    for event in pygame.event.get():
        if event.type == QUIT:
            SHUTDOWN = True
            break
        if event.type == KEYDOWN:
            KEYS_PRESSED.add(event.key)
        if event.type == KEYUP:
            KEYS_PRESSED.remove(event.key)
    # Handle player movement
    dx, dy = 0, 0
    if K_UP in KEYS_PRESSED:
        dy += 50/dt
    elif K_DOWN in KEYS_PRESSED:
        dy -= 50/dt
    elif K_RIGHT in KEYS_PRESSED:
        dx += 50/dt
    elif K_LEFT in KEYS_PRESSED:
        dx -= 50/dt
    # Create a client activity for the player's movement
    old_position = CONNECTION.game_state.players[PLAYER_ID]['position']
    move_activity = pygase.shared.ClientActivity(
        activity_type=pygase.shared.ActivityType.MovePlayer,
        activity_data={
            'player_id': PLAYER_ID,
            'new_position': (
                (old_position[0] + dx) % SCREEN_WIDTH,
                (old_position[1] + dy) % SCREEN_HEIGHT
            )
        }
    )
    # Do the thing.
    pygame.display.update()
```

Have Fun.