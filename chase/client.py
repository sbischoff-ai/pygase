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
# You need to disconnect from the server.
CONNECTION.disconnect()