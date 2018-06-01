<h1 id="pygase">pygase</h1>


<h1 id="pygase.shared">pygase.shared</h1>


This module contains classes for game objects that are relevant for both client and server:
*GameState*, *GameStateUpdate* and *ClientActivity*.
Client as well as server are supposed to define subclasses of classes in this module,
that extend those types with data and functionality that is client-/server-specific.

Also, this module defines the network protocol which *GameServiceConnection*s and *GamerService*s use
to communicate. It contains the *UDPPackage* class, which represents a unit of information
that client and server can exchange with each other, as well as classes that make up parts
of a package.

<h2 id="pygase.shared.TypeClass">TypeClass</h2>

```python
TypeClass(self, /, *args, **kwargs)
```

Mixin that allows to add class variables to a class during runtime.
It is used to make enum classes like AktivityType or PackageType extensible.

<h3 id="pygase.shared.TypeClass.add_type">add_type</h3>

```python
TypeClass.add_type(name:str)
```

Add a new named type to this enum-like class.

<h2 id="pygase.shared.Sendable">Sendable</h2>

```python
Sendable(self, /, *args, **kwargs)
```

Mixin for classes that are supposed to be sendable as part of a server request or response.
Sendables can only have basic Python types as attributes and their constructor needs
to be callable without passing any arguments.

<h3 id="pygase.shared.Sendable.from_bytes">from_bytes</h3>

```python
Sendable.from_bytes(bytepack:bytes)
```

Returns a copy of the object that was packed into byte format.

<h3 id="pygase.shared.Sendable.to_bytes">to_bytes</h3>

```python
Sendable.to_bytes(self)
```

Packs and return a small a binary representation of self.


<h2 id="pygase.shared.GameStatus">GameStatus</h2>

```python
GameStatus(self, /, *args, **kwargs)
```

Enum class with the values:
- *Paused*
- *Active*

<h2 id="pygase.shared.ActivityType">ActivityType</h2>

```python
ActivityType(self, /, *args, **kwargs)
```

Enum class with the values:
- *PauseGame*
- *ResumeGame*

<h2 id="pygase.shared.PackageType">PackageType</h2>

```python
PackageType(self, /, *args, **kwargs)
```

Enum class with the following values:
- *GetGameStateRequest*: As client request the full shared game state from the server.
    body = None
- *GetGameStateUpdateRequest*: As client request all polled game state updates.
    body = *GameStateUpdate* (purely for time-ordering)
- *PostClientActivityRequest*: As client post client-side activity to the *GameService*.
    body = *ClientActivity*
- *ServerResponse*: As server respond to a client request.
    body = request-dependent
- *ServerError*: As server report an error to the client.
    body = *ErrorMessage*

<h2 id="pygase.shared.ErrorType">ErrorType</h2>

```python
ErrorType(self, /, *args, **kwargs)
```

Enum class with the following values:
- *RequestTimeout*: Server _response took to long.
- *UnpackError*: Request or _response bytepack corrupted.
- *RequestInvalid*: Server could not handle the request.

To be used as part of an *ErrorMessage* object in a *ServerError* package.

<h2 id="pygase.shared.ErrorMessage">ErrorMessage</h2>

```python
ErrorMessage(self, error_type=<function ErrorType.RequestInvalid at 0x000001F38ABFDD90>, message='')
```

The sendable type *ErrorMessage* is used for the body of *UDPPackage*s with
*package_type* *PackageType.ServerError* in their *header*.

<h2 id="pygase.shared.UDPPackage">UDPPackage</h2>

```python
UDPPackage(self, package_type:pygase.shared.PackageType, body:pygase.shared.Sendable=None)
```

Contains *header* and *body* as attributes. The header contains information about the the
package type and body. The body is some object of a core class like *ErrorMessage*,
*GameState*, *GameStateUpdate* or *ClientActivity*.

<h3 id="pygase.shared.UDPPackage.from_datagram">from_datagram</h3>

```python
UDPPackage.from_datagram(datagram:bytes)
```

Unpacks the given bytepacked datagram and returns it's content as a *UDPPackage*
object.

<h3 id="pygase.shared.UDPPackage.to_datagram">to_datagram</h3>

```python
UDPPackage.to_datagram(self)
```

Returns a bytepacked datagram representing the UDPPackage.

<h3 id="pygase.shared.UDPPackage.is_response">is_response</h3>

```python
UDPPackage.is_response(self)
```

Returns *True* if the package is of package type *ServerResponse*.

<h3 id="pygase.shared.UDPPackage.is_error">is_error</h3>

```python
UDPPackage.is_error(self)
```

Returns *True* if the package is of package type *ServerError*.

<h3 id="pygase.shared.UDPPackage.is_update_request">is_update_request</h3>

```python
UDPPackage.is_update_request(self)
```

Returns *True* if the package is of package type *GetGameStateUpdateRequest*.

<h3 id="pygase.shared.UDPPackage.is_state_request">is_state_request</h3>

```python
UDPPackage.is_state_request(self)
```

Returns *True* if the package is of package type *GetGameStateRequest*.

<h3 id="pygase.shared.UDPPackage.is_post_activity_request">is_post_activity_request</h3>

```python
UDPPackage.is_post_activity_request(self)
```

Returns *True* if the package is of package type *PostClientActivityRequest*.

<h2 id="pygase.shared.GameState">GameState</h2>

```python
GameState(self, time_order=0, game_status=<function GameStatus.Paused at 0x000001F38ABFDBF8>)
```

Contains game state information that is required to be known both by the server and the client.
Since it is a *Sendable*, it can only contain basic python types as attributes.

*time_order* should be in alignment with the servers current update counter.

<h3 id="pygase.shared.GameState.is_paused">is_paused</h3>

```python
GameState.is_paused(self)
```

Returns *True* if game status is *Paused*.

<h2 id="pygase.shared.GameStateUpdate">GameStateUpdate</h2>

```python
GameStateUpdate(self, time_order=0, **kwargs)
```

Represents a set of changes to carry out on a *GameState*.
The server should keep an update counter and label all updated with ascending index.

Keywords are *GameState* atttribute names.

Use the *+* operator to add *GameStateUpdate*s together or to add them to a
*GameState* (returning the updated update/state).

Adding up available updates will always result in an equally or more current but
also heavier update (meaning it will contain more data).

<h2 id="pygase.shared.ClientActivity">ClientActivity</h2>

```python
ClientActivity(self, activity_type=<function ActivityType.PauseGame at 0x000001F38ABFDC80>, activity_data={})
```

An update the client sends to the server about client-side processes like player movement and
collisions. The server will validate *ClientActivity* samples and respond with an *OutOfSync*
error, if they contradict the server-side game state.

*activity_data* is a *dict* object, that contains all necessary information to process the
activity server-side (a player's *id*, *position* and *velocity* for example).

<h2 id="pygase.shared.join_server_activity">join_server_activity</h2>

```python
join_server_activity(player_name:str)
```

Returns a *ClientActivity* that joins a player with name *player_name* to the game.

<h2 id="pygase.shared.timeout_error">timeout_error</h2>

```python
timeout_error(message='')
```

Returns a *UDPPackage* with package type *ServerError*,
error type *RequestTimeout* and *message* as error message.

<h2 id="pygase.shared.unpack_error">unpack_error</h2>

```python
unpack_error(message='')
```

Returns a *UDPPackage* with package type *ServerError*,
error type *UnpackError* and *message* as error message.

<h2 id="pygase.shared.request_invalid_error">request_invalid_error</h2>

```python
request_invalid_error(message='')
```

Returns a *UDPPackage* with package type *ServerError*,
error type *RequestInvalid* and *message* as error message.

<h2 id="pygase.shared.game_state_request">game_state_request</h2>

```python
game_state_request()
```

Returns a *UDPPackage* with package type *GetGameStateRequest*.

<h2 id="pygase.shared.game_state_update_request">game_state_update_request</h2>

```python
game_state_update_request(time_order:int)
```

Returns a *UDPPackage* with package type *GetGameStateUpdateRequest*.
Enter the *time_order* attribute of the client's last known *GameState*.

<h2 id="pygase.shared.post_activity_request">post_activity_request</h2>

```python
post_activity_request(client_activity:pygase.shared.ClientActivity)
```

Returns a *UDPPackage* with package type *PostClientActivityRequest* with
the given *ClientActivity* object as it's body.

<h2 id="pygase.shared.response">response</h2>

```python
response(body:pygase.shared.Sendable)
```

Returns a *UDPPackage* with package type *ServerResponse*.

<h2 id="pygase.shared.toggle_pause_activity">toggle_pause_activity</h2>

```python
toggle_pause_activity(shared_game_state:pygase.shared.GameState)
```

Returns a *ClientActivity* that either pauses or resumes the server's game loop, depending
on the *game_status* of the given *GameState*.

