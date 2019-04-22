import time
import pygame, pygame.locals
from pygase import Client

client = Client()
client.connect_in_thread(hostname='localhost', port=8080)

# Join a new player to the server.
player_name = input('Player name: ')
client.dispatch_event(event_type='JOIN', handler_args=[player_name])

for _ in range(5):
    with client.access_game_state() as game_state:
        print(game_state.__dict__)
    time.sleep(1)

# Get the player's ID.
local_player_id = None
while local_player_id is None:
    with client.access_game_state() as game_state:
        for player_id, player in game_state.players.items():
            if player['name'] == player_name:
                local_player_id = player_id

# Little function to draw players as colored circles
# Green: Yourself
# Blue: Others
# Red: The chaser
def draw_player(screen, position, is_chaser, is_self):
    if is_self:
        color = (50, 255, 50)
    else:
        color = (255, 50, 50) if is_chaser else (50, 50, 255)
    pygame.draw.circle(screen, color, position, 10)

# Keep track of pressed keys.
keys_pressed = set()
# Keep track of time.
clock = pygame.time.Clock()

def game_loop():
        
    # Initialize a pygame screen
    pygame.init()
    screen_width = 640
    screen_height = 420
    screen = pygame.display.set_mode((screen_width, screen_height))

    while True:
        dt = clock.tick(40)
        # Clear the screen and draw all players
        screen.fill((0, 0, 0))
        with client.access_game_state() as game_state:
            for player_id, player in game_state.players.items():
                is_chaser = player_id == game_state.chaser
                is_self = player_id == local_player_id
                draw_player(screen, player['position'], is_chaser, is_self)
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                return
            if event.type == pygame.locals.KEYDOWN:
                keys_pressed.add(event.key)
            if event.type == pygame.locals.KEYUP:
                keys_pressed.remove(event.key)
        # Handle player movement
        dx, dy = 0, 0
        if pygame.locals.K_DOWN in keys_pressed:
            dy += int(0.1*dt)
        elif pygame.locals.K_UP in keys_pressed:
            dy -= int(0.1*dt)
        elif pygame.locals.K_RIGHT in keys_pressed:
            dx += int(0.1*dt)
        elif pygame.locals.K_LEFT in keys_pressed:
            dx -= int(0.1*dt)
        # Create a client activity for the player's movement
        with client.access_game_state() as game_state:
            old_position = game_state.players[local_player_id]['position']
            client.dispatch_event(
                event_type='MOVE',
                player_id=local_player_id,
                new_position=(
                    (old_position[0] + dx) % screen_width,
                    (old_position[1] + dy) % screen_height
                )
            )
        # Do the thing.
        pygame.display.flip()

    pygame.quit()

game_loop()
# You need to disconnect from the server.
client.disconnect(shutdown_server=True)
