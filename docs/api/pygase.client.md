<h1 id="pygase">pygase</h1>


<h1 id="pygase.client">pygase.client</h1>


This module mainly contains the *Connection* class, which represents a connection to a
running *Server*. Use this to manage your server connections.

**Note: If you want to connect to a server in another local network you must use the proper IPv4
address of that network, and not the local IP address of the server. Also the port on port on
which the *Server* serves has to be properly forwarded within that network.**

<h2 id="pygase.client.ConnectionStatus">ConnectionStatus</h2>

```python
ConnectionStatus(self, /, *args, **kwargs)
```

Enum class with the following values:
- *Connected*: Connection is running.
- *WaitingForServer*: Connection is trying to connect/reconnect to the server.
- *Disconnected*: Connection is not communicating with the server.

<h2 id="pygase.client.Connection">Connection</h2>

```python
Connection(self, server_address, closed=False)
```

Initialization of a *Connection* will open a connection to a BossFight Server
with the specified *server_address* as a tuple containing the IP-adress as a string and the
port as an int. Check the *connection_status* attribute to get the status of the Connection as
a *ConnectionStatus* attribute.

A running *Connection* will request an update of *game_state* from the server
every *update_cycle_interval* seconds.

<h3 id="pygase.client.Connection.connect">connect</h3>

```python
Connection.connect(self)
```

Will try to connect/reconnect to the server if *connection_status* is
*ConnectionStatus.Disconnected*, otherwise does nothing.

<h3 id="pygase.client.Connection.disconnect">disconnect</h3>

```python
Connection.disconnect(self)
```

Will stop the connection from sending any further requests to the server.
Will do nothing if *connection_status* == *ConnectionStatus.Disconnected*.

<h3 id="pygase.client.Connection.is_connected">is_connected</h3>

```python
Connection.is_connected(self)
```

Returns *True* if the connection status is *Connected*.

<h3 id="pygase.client.Connection.is_waiting">is_waiting</h3>

```python
Connection.is_waiting(self)
```

Returns *True* if the connection status is *WaitingForServer*.

<h3 id="pygase.client.Connection.post_client_activity">post_client_activity</h3>

```python
Connection.post_client_activity(self, client_activity:pygase.shared.ClientActivity)
```

Sends the *ClientActivity* object to the server.

