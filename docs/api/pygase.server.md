<h1 id="pygase">pygase</h1>


<h1 id="pygase.server">pygase.server</h1>


This module defines the *Server* class, a server that can handle requests from
a client's *ServerConnection* object and the *GameLoop*, which simulates the game logic.

**Note: The IP address you bind the Server to is a local IP address from the
192.168.x.x address space. If you want computers outside your local network to be
able to connect to your game server, you will have to forward the port from the local
address your server is bound to to your external IPv4 address!**

<h2 id="pygase.server.Server">Server</h2>

```python
Server(self, ip_address:str, port:int, game_loop_class:type, game_state:pygase.shared.GameState)
```

Threading UDP server that manages clients and processes requests.
*game_loop_class* is your subclass of *GameLoop*, which implements the handling of activities
and the game state update function. *game_state* is an instance of *pygase.shared.GameState* that
holds all necessary initial data.

Call *serve_forever*() in a seperate thread for the server to start handling requests from
*ServerConnection*s. Call *shutdown*() to stop it.

*game_loop* is the server's *GameLoop* object, which simulates the game logic and updates
the *game_state*.

<h3 id="pygase.server.Server.start">start</h3>

```python
Server.start(self)
```

Runs the server in a dedicated Thread and starts the game loop.
Does nothing if server is already running.
Must be called for the server to handle requests and is terminated by *shutdown()*

<h3 id="pygase.server.Server.shutdown">shutdown</h3>

```python
Server.shutdown(self)
```

Stops the server's request handling and pauses the game loop.

<h3 id="pygase.server.Server.get_ip_address">get_ip_address</h3>

```python
Server.get_ip_address(self)
```

Returns the servers IP address as a string.

<h3 id="pygase.server.Server.get_port">get_port</h3>

```python
Server.get_port(self)
```

Returns the servers port as an integer.

<h2 id="pygase.server.GameLoop">GameLoop</h2>

```python
GameLoop(self, server:pygase.server.Server)
```

Class that can update a shared game state by running a game logic simulation thread.
It must be passed a *pygase.shared.GameState* and a list of *pygase.shared.ClientActivity*s from the
*Server* object which owns the *GameLoop*.

You should inherit from this class and implement the *handle_activity()* and
*update_game_state()* methods.

<h3 id="pygase.server.GameLoop.start">start</h3>

```python
GameLoop.start(self)
```

Starts a thread that updates the shared game state every *update_cycle_interval* seconds.
Use this to restart a paused game.

<h3 id="pygase.server.GameLoop.pause">pause</h3>

```python
GameLoop.pause(self)
```

Stops the game loop until *start()* is called.
If the game loop is not currently running does nothing.

<h3 id="pygase.server.GameLoop.on_join">on_join</h3>

```python
GameLoop.on_join(self, player_id:int, update:pygase.shared.GameStateUpdate)
```

Override this method to define your initial player data.

<h3 id="pygase.server.GameLoop.handle_activity">handle_activity</h3>

```python
GameLoop.handle_activity(self, activity:pygase.shared.ClientActivity, update:pygase.shared.GameStateUpdate, dt)
```

Override this method to implement handling of client activities. Any state changes should be
written into the update argument of this method.

<h3 id="pygase.server.GameLoop.update_game_state">update_game_state</h3>

```python
GameLoop.update_game_state(self, update:pygase.shared.GameStateUpdate, dt)
```

Override to implement an iteration of your game logic simulation.
State changes should be written into the update argument.
Attributes of the shared game state that do not change at all, should not
be assigned to *update* (in order to optimize network performance).

