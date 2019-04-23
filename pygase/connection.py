# -*- coding: utf-8 -*-
"""
This module contains the low-level network logic of PyGaSe and is not supposed to be required
by any users of this library.
"""

import time

import curio
from curio import socket
from curio.meta import awaitable, iscoroutinefunction

from pygase.utils import Sendable, NamedEnum, sqn, LockedRessource
from pygase.event import Event
from pygase.gamestate import GameState, GameStateUpdate


class ProtocolIDMismatchError(ValueError):
    pass


class DuplicateSequenceError(ConnectionError):
    pass


class Package:
    """
    A network package that implements the PyGaSe protocol and is created, sent, received and resolved by
    PyGaSe **Connections**s.

    #### Arguments
     - **sequence** *int*: sequence number of the package on its senders side of the connection
     - **ack** *int*: sequence number of the last received package from the recipients side of the connection
    A sequence of `0` means no packages have been sent or received.
    After `65535` sequence numbers wrap around to `1`, so they can be stored in 2 bytes.
     - **ack_bitfield** *str*: A 32 character string representing the 32 packages prior to `remote_sequence`,
       with the first character corresponding the packge directly preceding it and so forth.
       `'1'` means the package has been received, `'0'` means it hasn't.

    #### Optional Arguments
     - **events** *[Event]*: list of PyGaSe events that is to be attached to this package and sent via network

    #### Class Attributes
     - **timeout** *float*: time in seconds after which a package is considered to be lost, `1.0` by default
     - **max_size** *int*: maximum size in bytes a package may have, `2048` by default

    #### Attributes
     - **sequence** *sqn*: packages sequence number
     - **ack** *sqn*: last received remote sequence number
     - **ack_bitfield** *str*: acknowledgement status of 32 preceding remote sequence numbers as boolean bitstring
    
    #### Properties
     - **events**: iterable of **Event** objects contained in the package
    """

    timeout = 1.0  # package timeout in seconds
    max_size = 2048  # the maximum size of PyGaSe package in bytes
    _protocol_id = bytes.fromhex("ffd0fab9")  # unique 4 byte identifier for pygase packages

    def __init__(self, sequence: int, ack: int, ack_bitfield: str, events: list = None):
        self.sequence = sqn(sequence)
        self.ack = sqn(ack)
        self.ack_bitfield = ack_bitfield
        self._events = events if events is not None else []
        self._datagram = None

    @property
    def events(self):
        return self._events.copy()

    def add_event(self, event: Event):
        """
        #### Arguments
         - **event** *Event*: a PyGaSe event that is to be attached to this package
        
        #### Raises
         - **OverflowError**: if the package had previously been converted to a datagram and
           and its size with the added event would exceed **max_size**
        """
        if self._datagram is not None:
            bytepack = event.to_bytes()
            if len(self._datagram) + len(bytepack) + 2 > self.max_size:
                raise OverflowError("package exceeds the maximum size of " + str(self.max_size) + " bytes")
            self._datagram += len(bytepack).to_bytes(2, "big") + bytepack
        self._events.append(event)

    def get_bytesize(self):
        """
        #### Returns
        *int*: size of the package as a datagram in bytes
        """
        if self._datagram is None:
            self._datagram = self.to_datagram()
        return len(self._datagram)

    def to_datagram(self):
        """
        #### Returns
        *bytes*: compact bytestring representing the package, which can be sent via a datagram socket
        
        #### Raises
         - **OverflowError**: if the resulting datagram would exceed **max_size**
        """
        if self._datagram is not None:
            return self._datagram
        datagram = self._create_header()
        # The header makes up the first 12 bytes of the package
        datagram.extend(self._create_event_block())
        datagram = bytes(datagram)
        if len(datagram) > self.max_size:
            raise OverflowError("package exceeds the maximum size of " + str(self.max_size) + " bytes")
        self._datagram = bytes(datagram)
        return self._datagram

    def _create_header(self):
        header = bytearray(self._protocol_id)
        header.extend(self.sequence.to_bytes())
        header.extend(self.ack.to_bytes())
        header.extend(int(self.ack_bitfield, 2).to_bytes(4, "big"))
        return header

    def _create_event_block(self):
        event_block = bytearray()
        for event in self._events:
            bytepack = event.to_bytes()
            event_block.extend(len(bytepack).to_bytes(2, "big"))
            event_block.extend(bytepack)
        return event_block

    @classmethod
    def from_datagram(cls, datagram: bytes):
        """
        #### Arguments
         - **datagram** *bytes*: bytestring data, typically received via a socket
        
        #### Returns
        *Package*: the package from which the datagram has been created using `to_datagram()`

        #### Raises
         - **ProtocolIDMismatchError**: if the first four bytes don't match the PyGaSe protocol ID
        """
        header_args, payload = cls._read_out_header(datagram)
        events = cls._read_out_event_block(payload)
        result = Package(**header_args, events=events)
        result._datagram = datagram
        return result

    @classmethod
    def _read_out_header(cls, datagram):
        if datagram[:4] != cls._protocol_id:
            raise ProtocolIDMismatchError
        sequence = sqn.from_bytes(datagram[4:6])
        ack = sqn.from_bytes(datagram[6:8])
        ack_bitfield = bin(int.from_bytes(datagram[8:12], "big"))[2:].zfill(32)
        payload = datagram[12:]
        return ({"sequence": sequence, "ack": ack, "ack_bitfield": ack_bitfield}, payload)

    @staticmethod
    def _read_out_event_block(event_block):
        events = []
        while len(event_block) > 0:
            bytesize = int.from_bytes(event_block[:2], "big")
            events.append(Event.from_bytes(event_block[2 : bytesize + 2]))
            event_block = event_block[bytesize + 2 :]
        return events

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class ClientPackage(Package):
    """
    Subclass of **Package** that describes packages sent by **ClientConnection**s.

    #### Arguments
     - **time_order** *int/sqn*: the clients last known time order 
    """

    def __init__(self, sequence: int, ack: int, ack_bitfield: str, time_order: int, events: list = None):
        super().__init__(sequence, ack, ack_bitfield, events)
        self.time_order = sqn(time_order)

    def to_datagram(self):
        """
        #### Returns
        *bytes*: compact bytestring representing the package, which can be sent via a datagram socket
        
        #### Raises
         - **OverflowError**: if the resulting datagram would exceed **max_size**
        """
        if self._datagram is not None:
            return self._datagram
        datagram = self._create_header()
        # The header makes up the first 12 bytes of the package
        datagram.extend(self.time_order.to_bytes())
        datagram.extend(self._create_event_block())
        datagram = bytes(datagram)
        if len(datagram) > self.max_size:
            raise OverflowError("package exceeds the maximum size of " + str(self.max_size) + " bytes")
        self._datagram = bytes(datagram)
        return self._datagram

    @classmethod
    def from_datagram(cls, datagram):
        """
        #### Arguments
         - **datagram** *bytes*: bytestring data, typically received via a socket
        
        #### Returns
        *Package*: the package from which the datagram has been created using `to_datagram()`

        #### Raises
         - **ProtocolIDMismatchError**: if the first four bytes don't match the PyGaSe protocol ID
        """
        header_args, payload = cls._read_out_header(datagram)
        time_order = sqn.from_bytes(payload[:2])
        payload = payload[2:]
        events = cls._read_out_event_block(payload)
        result = ClientPackage(**header_args, time_order=time_order, events=events)
        result._datagram = datagram
        return result


class ServerPackage(Package):
    """
    Subclass of **Package** that describes packages sent by **ServerConnection**s.

    #### Arguments
     - **game_state_update** *GameStateUpdate*: the servers most recent minimal update for the client 
    """

    def __init__(
        self, sequence: int, ack: int, ack_bitfield: str, game_state_update: GameStateUpdate, events: list = None
    ):
        super().__init__(sequence, ack, ack_bitfield, events)
        self.game_state_update = game_state_update

    def to_datagram(self):
        """
        #### Returns
        *bytes*: compact bytestring representing the package, which can be sent via a datagram socket
        
        #### Raises
         - **OverflowError**: if the resulting datagram would exceed **max_size**
        """
        if self._datagram is not None:
            return self._datagram
        datagram = self._create_header()
        # The header makes up the first 12 bytes of the package
        state_update_bytepack = self.game_state_update.to_bytes()
        datagram.extend(len(state_update_bytepack).to_bytes(2, "big"))
        datagram.extend(state_update_bytepack)
        datagram.extend(self._create_event_block())
        datagram = bytes(datagram)
        if len(datagram) > self.max_size:
            raise OverflowError("package exceeds the maximum size of " + str(self.max_size) + " bytes")
        self._datagram = bytes(datagram)
        return self._datagram

    @classmethod
    def from_datagram(cls, datagram):
        """
        #### Arguments
         - **datagram** *bytes*: bytestring data, typically received via a socket
        
        #### Returns
        *Package*: the package from which the datagram has been created using `to_datagram()`

        #### Raises
         - **ProtocolIDMismatchError**: if the first four bytes don't match the PyGaSe protocol ID
        """
        header_args, payload = cls._read_out_header(datagram)
        state_update_bytesize = int.from_bytes(payload[:2], "big")
        game_state_update = GameStateUpdate.from_bytes(payload[2 : state_update_bytesize + 2])
        payload = payload[state_update_bytesize + 2 :]
        events = cls._read_out_event_block(payload)
        result = ServerPackage(**header_args, game_state_update=game_state_update, events=events)
        result._datagram = datagram
        return result


class ConnectionStatus(NamedEnum):
    pass


ConnectionStatus.register("Disconnected")
ConnectionStatus.register("Connected")
ConnectionStatus.register("Connecting")


class Connection:
    """
    This class resembles a client-server connection via the PyGaSe protocol.

    #### Arguments
     - **remote_address** *(str, int)*: A tuple `('hostname', port)` *required*
     - **event_handler**: An object that has a callable `handle()` attribute that takes
       an **Event** as argument, for example a **PyGaSe.event.UniversalEventHandler** instance
     - **event_wire**: object to which events are to be repeated (has to implement a *_push_event* method)

    #### Attributes
     - **remote_address** *(str, int)*: A tuple `('hostname', port)`
     - **local_sequence** *int*: sequence number of the last sent package
     - **remote_sequence** *int*: sequence number of the last received package
    A sequence of `0` means no packages have been sent or received.
    After `65535` sequence numbers wrap around to `1`, so they can be stored in 2 bytes.
     - **ack_bitfield** *str*: A 32 character string representing the 32 packages prior to `remote_sequence`,
        with the first character corresponding the packge directly preceding it and so forth.
        `'1'` means the package has been received, `'0'` means it hasn't.
     - **latency**: the last registered RTT (round trip time)
     - **status** *int*: A **ConnectionStatus** value.
     - **quality** *str*: Either `'good'` or `'bad'`, depending on latency. Is used internally for
        congestion avoidance.
    """

    timeout = 5.0  # connection timeout in seconds
    max_throttle_time = 60.0
    min_throttle_time = 1.0
    _package_intervals = {
        "good": 1 / 40,
        "bad": 1 / 20,
    }  # maps connection.quality to time between sent packages in seconds
    _latency_threshold = 0.25  # latency that will trigger connection throttling

    def __init__(self, remote_address: tuple, event_handler, event_wire=None):
        self.remote_address = remote_address
        self.event_handler = event_handler
        self.local_sequence = sqn(0)
        self.remote_sequence = sqn(0)
        self.ack_bitfield = "0" * 32
        self.latency = 0.0
        self.status = ConnectionStatus.get("Connecting")
        self.package_interval = self._package_intervals["good"]
        self.quality = "good"  # this is used for congestion avoidance
        self._outgoing_event_queue = curio.UniversalQueue()
        self._incoming_event_queue = curio.UniversalQueue()
        self._pending_acks = {}
        self._event_callback_sequence = sqn(0)
        self._events_with_callbacks = {}
        self._event_callbacks = {}
        self._last_recv = time.time()
        self._event_wire = event_wire

    def _update_remote_info(self, received_sequence):
        if self.remote_sequence == 0:
            self.remote_sequence = received_sequence
            return
        sequence_diff = self.remote_sequence - received_sequence
        if sequence_diff < 0:
            self.remote_sequence = received_sequence
            if sequence_diff == -1:
                self.ack_bitfield = "1" + self.ack_bitfield[:-1]
            else:
                self.ack_bitfield = self.ack_bitfield[:sequence_diff].zfill(32)
        if sequence_diff == 0:
            raise DuplicateSequenceError
        elif sequence_diff > 0:
            if self.ack_bitfield[sequence_diff - 1] == "1":
                raise DuplicateSequenceError
            else:
                self.ack_bitfield = self.ack_bitfield[: sequence_diff - 1] + "1" + self.ack_bitfield[sequence_diff:]

    async def _recv(self, received_package: Package):
        """
        Updates `remote_sequence` and `ack_bitfield` based on a received package, resolves package loss
        and puts the received events in the queue of incoming events.
        
        #### Raises
         - **DuplicateSequenceError**: if a package with the same sequence has already been received
        """
        self._last_recv = time.time()
        self._set_status("Connected")
        self._update_remote_info(received_package.sequence)
        # resolve pending acks for sent packages (NEEDS REFACTORING)
        for pending_sequence in list(self._pending_acks):
            sequence_diff = received_package.ack - pending_sequence
            if sequence_diff == 0 or (
                0 < sequence_diff < 32 and received_package.ack_bitfield[sequence_diff - 1] == "1"
            ):
                self._update_latency(time.time() - self._pending_acks[pending_sequence])
                if pending_sequence in self._events_with_callbacks:
                    for event_sequence in self._events_with_callbacks[pending_sequence]:
                        if self._event_callbacks[event_sequence]["ack"] is not None:
                            if iscoroutinefunction(self._event_callbacks[event_sequence]["ack"]):
                                await self._event_callbacks[event_sequence]["ack"]()
                            else:
                                self._event_callbacks[event_sequence]["ack"]()
                            del self._event_callbacks[event_sequence]
                    del self._events_with_callbacks[pending_sequence]
                del self._pending_acks[pending_sequence]
            elif time.time() - self._pending_acks[pending_sequence] > Package.timeout:
                if pending_sequence in self._events_with_callbacks:
                    for event_sequence in self._events_with_callbacks[pending_sequence]:
                        if self._event_callbacks[event_sequence]["timeout"] is not None:
                            if iscoroutinefunction(self._event_callbacks[event_sequence]["timeout"]):
                                await self._event_callbacks[event_sequence]["timeout"]()
                            else:
                                self._event_callbacks[event_sequence]["timeout"]()
                            del self._event_callbacks[event_sequence]
                    del self._events_with_callbacks[pending_sequence]
                del self._pending_acks[pending_sequence]
        for event in received_package.events:
            await self._incoming_event_queue.put(event)
            if self._event_wire is not None:
                await self._event_wire._push_event(event)

    def dispatch_event(self, event: Event, ack_callback=None, timeout_callback=None):
        """
        #### Arguments
         - **event** *Event*: the event to be sent to connection partner
        
        #### Optional Arguments
         - **ack_callback**: function or coroutine to be executed after the event was received
         - **timeout_callback**: function or coroutine to be executed if the event was not received
        """
        callback_sequence = 0
        if ack_callback is not None or timeout_callback is not None:
            self._event_callback_sequence += 1
            callback_sequence = self._event_callback_sequence
            self._event_callbacks[self._event_callback_sequence] = {"ack": ack_callback, "timeout": timeout_callback}
        self._outgoing_event_queue.put((event, callback_sequence))

    async def _handle_next_event(self):
        event = await self._incoming_event_queue.get()
        if self.event_handler.has_type(event.type):
            await self.event_handler.handle(event)
        await self._incoming_event_queue.task_done()

    async def _event_loop(self):
        while True:
            await self._handle_next_event()

    async def _send_loop(self, sock):
        """
        Coroutine that, once spawned, will keep sending packages to the remote_address until it is explicitly
        cancelled or the connection times out.
        """
        congestion_avoidance_task = await curio.spawn(self._congestion_avoidance_monitor)
        while True:
            t0 = time.time()
            if t0 - self._last_recv > self.timeout:
                self._set_status("Disconnected")
                break
            await self._send_next_package(sock)
            await curio.sleep(max([self.package_interval - time.time() + t0, 0]))
        await congestion_avoidance_task.cancel()

    def _create_next_package(self):
        return Package(self.local_sequence, self.remote_sequence, self.ack_bitfield)

    async def _send_next_package(self, sock):
        self.local_sequence += 1
        package = self._create_next_package()
        while len(package.events) < 5 and not self._outgoing_event_queue.empty():
            event, callback_sequence = await self._outgoing_event_queue.get()
            if callback_sequence != 0:
                if self.local_sequence not in self._events_with_callbacks:
                    self._events_with_callbacks[self.local_sequence] = [callback_sequence]
                else:
                    self._events_with_callbacks[self.local_sequence].append(callback_sequence)
            package.add_event(event)
            await self._outgoing_event_queue.task_done()
        await sock.sendto(package.to_datagram(), self.remote_address)
        self._pending_acks[package.sequence] = time.time()

    def _set_status(self, status: str):
        self.status = ConnectionStatus.get(status)

    def _update_latency(self, rtt: int):
        # smoothed moving average to filter out network jitter
        self.latency += 0.1 * (rtt - self.latency)

    async def _congestion_avoidance_monitor(self):
        state = {
            "throttle_time": self.min_throttle_time,
            "last_quality_change": time.time(),
            "last_good_quality_milestone": time.time(),
        }
        while True:
            self._throttling_state_machine(time.time(), state)
            await curio.sleep(Connection.min_throttle_time / 2.0)

    def _throttling_state_machine(self, t: int, state: dict):
        if self.quality == "good":
            if self.latency > self._latency_threshold:  # switch to bad mode
                self.quality = "bad"
                self.package_interval = self._package_intervals["bad"]
                # if good conditions didn't last at least the throttle time, increase it
                if t - state["last_quality_change"] < state["throttle_time"]:
                    state["throttle_time"] = min([state["throttle_time"] * 2.0, self.max_throttle_time])
                state["last_quality_change"] = t
            # if good conditions lasted throttle time since last milestone
            elif t - state["last_good_quality_milestone"] > state["throttle_time"]:
                self.package_interval = self._package_intervals["good"]
                state["throttle_time"] = max([state["throttle_time"] / 2.0, self.min_throttle_time])
                state["last_good_quality_milestone"] = t
        else:  # self.quality == 'bad'
            if self.latency < self._latency_threshold:  # switch to good mode
                self.quality = "good"
                state["last_quality_change"] = t
                state["last_good_quality_milestone"] = t


class ClientConnection(Connection):
    """
    Subclass of **Connection** that describes the client side of a PyGaSe connection.

    #### Attributes
     - **game_state_context** *LockedRessource*: provides thread-safe access to a *GameState* object
    """

    def __init__(self, remote_address, event_handler):
        super().__init__(remote_address, event_handler)
        self._command_queue = curio.UniversalQueue()
        self.game_state_context = LockedRessource(GameState())

    def shutdown(self, shutdown_server: bool = False):
        """
        Shuts down the client connection. (Can also be called as a coroutine.)

        #### Optional Arguments
         - **shutdown_server** *bool*: wether or not the server should be shut down too.
            (Only has an effect if the client has host permissions.)
        """
        curio.run(self.shutdown, shutdown_server)

    @awaitable(shutdown)
    async def shutdown(self, shutdown_server: bool = False):  # pylint: disable=function-redefined
        if shutdown_server:
            await self._command_queue.put("shutdown")
        else:
            await self._command_queue.put("shut_me_down")

    def _create_next_package(self):
        time_order = self.game_state_context.ressource.time_order
        return ClientPackage(self.local_sequence, self.remote_sequence, self.ack_bitfield, time_order)

    def loop(self):
        """
        The loop that will send and receive packages and handle events. (Can also be called as a coroutine.)
        """
        curio.run(self.loop)

    @awaitable(loop)
    async def loop(self):  # pylint: disable=function-redefined
        async with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            send_loop_task = await curio.spawn(self._send_loop, sock)
            recv_loop_task = await curio.spawn(self._client_recv_loop, sock)
            event_loop_task = await curio.spawn(self._event_loop)
            # check for disconnect event
            while True:
                command = await self._command_queue.get()
                if command == "shutdown":
                    await sock.sendto("shutdown".encode("utf-8"), self.remote_address)
                    break
                elif command == "shut_me_down":
                    break
            await recv_loop_task.cancel()
            await send_loop_task.cancel()
            await event_loop_task.cancel()
            self._set_status("Disconnected")

    async def _recv(self, package):
        await super()._recv(package)
        async with curio.abide(self.game_state_context.lock):
            self.game_state_context.ressource += package.game_state_update

    async def _client_recv_loop(self, sock):
        while self.local_sequence == 0:
            await curio.sleep(0)
        while True:
            data = await sock.recv(ServerPackage.max_size)
            package = ServerPackage.from_datagram(data)
            await self._recv(package)


class ServerConnection(Connection):
    """
    Subclass of **Connection** that describes the server side of a PyGaSe connection.

    #### Attributes
     - **game_state_store** *GameStateStore*: the backends **GameStateStore** that provides the state for this client
     - **last_client_time_order** *sqn*: the clients last known time order
    """

    def __init__(
        self, remote_address: tuple, event_handler, game_state_store, last_client_time_order: sqn, event_wire=None
    ):
        super().__init__(remote_address, event_handler, event_wire)
        self.game_state_store = game_state_store
        self.last_client_time_order = last_client_time_order

    def _create_next_package(self):
        update_cache = self.game_state_store.get_update_cache()
        # Respond by sending the sum of all updates since the client's time-order point.
        # Or the whole game state if the client doesn't have it yet.
        if self.last_client_time_order == 0:
            game_state = self.game_state_store.get_game_state()
            update = GameStateUpdate(**game_state.__dict__)
        else:
            update_base = GameStateUpdate(self.last_client_time_order)
            update = sum((upd for upd in update_cache if upd > update_base), update_base)
        return ServerPackage(self.local_sequence, self.remote_sequence, self.ack_bitfield, update)

    async def _recv(self, package: ClientPackage):
        await super()._recv(package)
        self.last_client_time_order = package.time_order

    @classmethod
    async def loop(cls, hostname: str, port: int, server, event_wire):
        """
        Coroutine that deals with a **Server**s connections to clients.

        #### Arguments
         - **hostname** *str*: the hostname to which to bind the server socket
         - **port** *int*: the port number to which to bind the server socket
         - **server** *Server*: the **Server** for which this loop is run
         - **event_wire**: object to which events are to be repeated
           (has to implement a *_push_event* method and is typically a **GameStateMachine**)
        """
        async with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind((hostname, port))
            server._hostname, server._port = sock.getsockname()
            connection_tasks = curio.TaskGroup()
            while True:
                data, client_address = await sock.recvfrom(Package.max_size)
                try:
                    package = ClientPackage.from_datagram(data)
                    # create new connection if client is unknown
                    if not client_address in server.connections:
                        new_connection = cls(
                            client_address,
                            server._universal_event_handler,
                            server.game_state_store,
                            package.time_order,
                            event_wire,
                        )
                        await connection_tasks.spawn(new_connection._send_loop, sock)
                        await connection_tasks.spawn(new_connection._event_loop)
                        # For now, the first client connection becomes host
                        if server.host_client is None:
                            server.host_client = client_address
                        server.connections[client_address] = new_connection
                    elif server.connections[client_address].status == ConnectionStatus.get("Disconnected"):
                        await connection_tasks.spawn(server.connections[client_address]._send_loop, sock)
                    await server.connections[client_address]._recv(package)
                except ProtocolIDMismatchError:
                    # ignore all non-PyGaSe packages
                    pass
                try:
                    if data.decode("utf-8") == "shutdown" and client_address == server.host_client:
                        break
                    elif data.decode("utf-8") == "shut_me_down":
                        break
                except UnicodeDecodeError:
                    pass
            await connection_tasks.cancel_remaining()
