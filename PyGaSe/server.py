# -*- coding: utf-8 -*-
'''
This module defines the *Server* class, a server that can handle requests from
a client's *ServerConnection* object and the *GameLoop*, which simulates the game logic.

**Note: The IP address you bind the Server to is a local IP address from the
192.168.x.x address space. If you want computers outside your local network to be
able to connect to your game server, you will have to forward the port from the local
address your server is bound to to your external IPv4 address!**
'''

import socketserver
import threading
import time
import math
import PyGaSe.shared

UPDATE_CACHE_SIZE = 100

class Server(socketserver.ThreadingUDPServer):
    '''
    Threading UDP server that manages clients and processes requests.
    *game_loop_class* is your subclass of *GameLoop*, which implements the handling of activities
    and the game state update function. *game_state* is an instance of *PyGaSe.shared.GameState* that
    holds all necessary initial data.

    Call *serve_forever*() in a seperate thread for the server to start handling requests from
    *ServerConnection*s. Call *shutdown*() to stop it.

    *game_loop* is the server's *GameLoop* object, which simulates the game logic and updates
    the *game_state*.
    '''

    def __init__(self, ip_address: str, port: int, game_loop_class: type, game_state: PyGaSe.shared.GameState):
        super().__init__((ip_address, port), ServerRequestHandler)
        self.game_state = game_state
        self._client_activity_queue = []
        self._state_update_cache = []
        self._player_counter = 0
        self.game_loop = GameLoop(self)
        self._server_thread = threading.Thread()

    def start(self):
        '''
        Runs the server in a dedicated Thread and starts the game loop.
        Does nothing if server is already running.
        Must be called for the server to handle requests and is terminated by *shutdown()*
        '''
        if not self._server_thread.is_alive():
            self._server_thread = threading.Thread(target=self.serve_forever)
            self.game_loop.start()
            self._server_thread.start()

    def shutdown(self):
        '''
        Stops the server's request handling and pauses the game loop.
        '''
        super().shutdown()
        self.game_loop.pause()

    def get_ip_address(self):
        '''
        Returns the servers IP address as a string.
        '''
        return self.socket.getsockname()[0]

    def get_port(self):
        '''
        Returns the servers port as an integer.
        '''
        return self.socket.getsockname()[1]

class ServerRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # Read out request
        try:
            request = PyGaSe.shared.UDPPackage.from_datagram(self.request[0])
        except TypeError:
            # if unpacking request failed send back error message and exit handle function
            response = PyGaSe.shared.unpack_error('Server responded: Byte error.')
            self.request[1].sendto(response.to_datagram(), self.client_address)
            return

        # Handle request and assign response here
        if request.is_update_request():
            # respond by sending the sum of all updates since the client's time-order point.
            update = sum(
                (upd for upd in self.server.game_loop._state_update_cache if upd > request.body),
                request.body
            )
            response = PyGaSe.shared.response(update)
        elif request.is_post_activity_request():
            # Pausing or Resuming the game and joining a server must be possible outside
            # of the game loop:
            if request.body.activity_type == PyGaSe.shared.ActivityType.PauseGame:
                self.server.game_loop.pause()
                self.server.game_state.time_order += 1
                self.server.game_loop._cache_state_update(PyGaSe.shared.GameStateUpdate(
                    time_order=self.server.game_state.time_order,
                    game_status=PyGaSe.shared.GameStatus.Paused
                ))
            elif request.body.activity_type == PyGaSe.shared.ActivityType.ResumeGame:
                self.server.game_state.time_order += 1
                self.server.game_loop._cache_state_update(PyGaSe.shared.GameStateUpdate(
                    time_order=self.server.game_state.time_order,
                    game_status=PyGaSe.shared.GameStatus.Active
                ))
                self.server.game_loop.start()
            elif request.body.activity_type == PyGaSe.shared.ActivityType.JoinServer:
                # A player dict is added to the game state. The id is unique for the
                # server session (counting from 0 upwards).
                update = PyGaSe.shared.GameStateUpdate(
                    time_order=self.server.game_state.time_order + 1,
                    players={
                        self.server._player_counter: {
                            'name': request.body.activity_data['name'],
                            'position': (0, 0),
                            'velocity': (0, 0)
                        }
                    }
                )
                self.server._player_counter += 1
                self.server.game_state += update
                self.server.game_loop._cache_state_update(update)
            else:
                # Any other kind of activity: add to the queue for the game loop
                self.server._client_activity_queue.append(request.body)
            response = PyGaSe.shared.response(None)
        elif request.is_state_request():
            # respond by sending back the shared game state
            response = PyGaSe.shared.response(self.server.game_state)
        else:
            # if none of the above were a match the request was invalid
            response = PyGaSe.shared.request_invalid_error('Server responded: Request invalid.')

        # Send response
        self.request[1].sendto(response.to_datagram(), self.client_address)

class GameLoop:
    '''
    Class that can update a shared game state by running a game logic simulation thread.
    It must be passed a *PyGaSe.shared.GameState* and a list of *PyGaSe.shared.ClientActivity*s from the
    *Server* object which owns the *GameLoop*.

    You should inherit from this class and implement the *handle_activity()* and
    *update_game_state()* methods.
    '''
    def __init__(self, server: Server):
        self.server = server
        self._game_loop_thread = threading.Thread()
        self.update_cycle_interval = 0.03

    def start(self):
        '''
        Starts a thread that updates the shared game state every *update_cycle_interval* seconds.
        Use this to restart a paused game.
        '''
        if not self._game_loop_thread.is_alive():
            self._game_loop_thread = threading.Thread(target=self._update_cycle)
            self.server.game_state.game_status = PyGaSe.shared.GameStatus.Active
            self._game_loop_thread.start()

    def pause(self):
        '''
        Stops the game loop until *start()* is called.
        If the game loop is not currently running does nothing.
        '''
        self.server.game_state.game_status = PyGaSe.shared.GameStatus.Paused

    def _update_cycle(self):
        dt = self.update_cycle_interval
        while not self.server.game_state.is_paused():
            t = time.time()
            # Create update object and fill it with all necessary changes
            update = PyGaSe.shared.GameStateUpdate(self.server.game_state.time_order + 1)
            # Handle client activities first
            activities_to_handle = self.server._client_activity_queue[:5]
            # Get first 5 activitys in queue
            for activity in activities_to_handle:
                self.handle_activity(activity, update, dt)
                del self.server._client_activity_queue[0]
                # Should be safe, otherwise use *remove(activity)*
            self.update_game_state(update, dt)
            # Add the update to the game state and cache it for the clients
            self.server.game_state += update
            self._cache_state_update(update)
            dt = time.time() - t
            time.sleep(max(self.update_cycle_interval-dt, 0))

    def handle_activity(self, activity: PyGaSe.shared.ClientActivity, update: PyGaSe.shared.GameStateUpdate, dt):
        '''
        Override this method to implement handling of client activities. Any state changes should be
        written into the update argument of this method.
        '''
        raise NotImplementedError
        #if activity.activity_type == PyGaSe.shared.ActivityType.MyActivtity:
        #    update.some_attribute = foo()
        #elif activity.activity_type == PyGaSe.shared.ActivityType.MyOtherActivity:
        #    update.other_attribute = bar()

    def update_game_state(self, update: PyGaSe.shared.GameStateUpdate, dt):
        '''
        Override to implement an iteration of your game logic simulation.
        State changes should be written into the update argument.
        Attributes of the shared game state that do not change at all, should not
        be assigned to *update* (in order to optimize network performance).
        '''
        raise NotImplementedError

    def _cache_state_update(self, state_update: PyGaSe.shared.GameStateUpdate):
        self.server._state_update_cache.append(state_update)
        if len(self.server._state_update_cache) > UPDATE_CACHE_SIZE:
            self.server._state_update_cache = self.server._state_update_cache[1:]
