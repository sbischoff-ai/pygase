# PyGaSe
**Py**thon**Ga**me**Se**rver

A Python package that contains a versatile lightweight UDP-based client-server API and network protocol for 
real-time online games.

Installation: `pip install pygase`

## Usage Example

This example game implements an online game of chase, in which players can move around,
while one of them is the chaser who has to catch another player. A player who has been
catched becomes the next chaser and can catch other players after a 5s protection countdown.

For a complete API documentation look in `.\docs\api\` (see GitHub if you're on PyPI.org).

### Shared

```Python
# shared_stuff.py

import pygase.shared

# Define your own client activities.
pygase.shared.ActivityType.add_type('MovePlayer')
```

### Server

```Python
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
```

### Client

```Python
import pygame, pygame.locals
import pygase.shared, pygase.client
import chase.shared_stuff

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
while PLAYER_ID is None:
    for player_id, player in CONNECTION.game_state.players.copy().items():
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
    else:
        color = (255, 50, 50) if is_chaser else (50, 50, 255)
    pygame.draw.circle(SCREEN, color, position, 10)

# Keep track of pressed keys.
KEYS_PRESSED = set()

# Keep track of time.
CLOCK = pygame.time.Clock()

# The client's game loop
SHUTDOWN = False
while not SHUTDOWN:
    dt = CLOCK.tick(40)
    # Clear the screen and draw all players
    SCREEN.fill((0, 0, 0))
    for player_id, player in CONNECTION.game_state.players.copy().items():
        is_chaser = player_id == CONNECTION.game_state.chaser
        is_self = player_id == PLAYER_ID
        draw_player(player['position'], is_chaser, is_self)
        # This will not produce smooth movement, especially not when the
        # connection is imperfect. If you want smoother movement, let the
        # client keep track of player positions seperately and each frame
        # update the client-side positions using a velocity that is
        # proportional to the distance between the servers and clients
        # version of that players position.
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.locals.QUIT:
            SHUTDOWN = True
            break
        if event.type == pygame.locals.KEYDOWN:
            KEYS_PRESSED.add(event.key)
        if event.type == pygame.locals.KEYUP:
            KEYS_PRESSED.remove(event.key)
    # Handle player movement
    dx, dy = 0, 0
    if pygame.locals.K_DOWN in KEYS_PRESSED:
        dy += int(0.1*dt)
    elif pygame.locals.K_UP in KEYS_PRESSED:
        dy -= int(0.1*dt)
    elif pygame.locals.K_RIGHT in KEYS_PRESSED:
        dx += int(0.1*dt)
    elif pygame.locals.K_LEFT in KEYS_PRESSED:
        dx -= int(0.1*dt)
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
    # Send the activity to the server.
    CONNECTION.post_client_activity(move_activity)
    # Do the thing.
    pygame.display.flip()

pygame.quit()
# Leave the server
CONNECTION.post_client_activity(
    pygase.shared.leave_server_activity(PLAYER_ID)
)
# You need to disconnect from the server.
CONNECTION.disconnect()
```

Have Fun.
