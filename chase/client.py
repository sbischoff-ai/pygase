'''
Example game client
'''

from curio import sleep
import pygame
import pygame.locals
from pygase import Client

class ChaseGame:
    client = Client()
    local_player_name = None
    local_player_id = None
    keys_pressed = set()
    clock = pygame.time.Clock()

    @classmethod
    def start(cls):
        '''Connect the client and join a new player to the server.'''
        cls.client.connect_in_thread(hostname='localhost', port=8080)
        cls.local_player_name = input('Player name: ')
        cls.client.dispatch_event(
            event_type='JOIN',
            handler_args=[cls.local_player_name],
            ack_callback=cls.game_loop
        )

    @classmethod
    async def game_loop(cls):
        '''
        Basically the whole game
        '''
        # Get the player's ID
        for _ in range(5):
            print(cls.client.connection.game_state_context.ressource.__dict__)
            print('---')
            await sleep(0.2)
        while cls.local_player_id is None:
            with cls.client.access_game_state() as game_state:
                for player_id, player in game_state.players.items():
                    if player['name'] == cls.local_player_name:
                        cls.local_player_id = player_id
                print(game_state.__dict__)
            print('---')
            await sleep(0.5)
        # Initialize a pygame screen
        pygame.init()
        screen_width = 640
        screen_height = 420
        screen = pygame.display.set_mode((screen_width, screen_height))
        # The actual game loop
        while True:
            dt = cls.clock.tick(40)
            # Clear the screen and draw all players
            screen.fill((0, 0, 0))
            with cls.client.access_game_state() as game_state:
                for player_id, player in game_state.players.items():
                    is_chaser = player_id == game_state.chaser
                    is_self = player_id == cls.local_player_id
                    draw_player(screen, player['position'], is_chaser, is_self)
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.locals.QUIT:
                    return
                if event.type == pygame.locals.KEYDOWN:
                    cls.keys_pressed.add(event.key)
                if event.type == pygame.locals.KEYUP:
                    cls.keys_pressed.remove(event.key)
            # Handle player movement
            dx, dy = 0, 0
            if pygame.locals.K_DOWN in cls.keys_pressed:
                dy += int(0.1*dt)
            elif pygame.locals.K_UP in cls.keys_pressed:
                dy -= int(0.1*dt)
            elif pygame.locals.K_RIGHT in cls.keys_pressed:
                dx += int(0.1*dt)
            elif pygame.locals.K_LEFT in cls.keys_pressed:
                dx -= int(0.1*dt)
            # Create a client activity for the player's movement
            with cls.client.access_game_state() as game_state:
                old_position = game_state.players[cls.local_player_id]['position']
                cls.client.dispatch_event(
                    event_type='MOVE',
                    player_id=cls.local_player_id,
                    new_position=(
                        (old_position[0] + dx) % screen_width,
                        (old_position[1] + dy) % screen_height
                    )
                )
            # Do the thing.
            pygame.display.flip()
            await sleep(0)
        pygame.quit()
        # You need to disconnect from the server
        cls.client.disconnect(shutdown_server=True)

    @staticmethod
    def draw_player(screen, position, is_chaser, is_self):
        '''
        Little function to draw players as colored circles
         - Green: Yourself
         - Blue: Others
         - Red: The chaser
        '''
        if is_self:
            color = (50, 255, 50)
        else:
            color = (255, 50, 50) if is_chaser else (50, 50, 255)
        pygame.draw.circle(screen, color, position, 10)

ChaseGame.start()
