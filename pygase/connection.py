# -*- coding: utf-8 -*-

import time

import curio
from curio import socket

from pygase.utils import Sendable, NamedEnum, sqn
from pygase.event import Event

class ProtocolIDMismatchError(ValueError): pass

class DuplicateSequenceError(ConnectionError): pass

class Package:
    '''
    A network package that implements the Pygase protocol and is created, sent, received and resolved by
    Pygase **Connections**s.

    ### Arguments
     - **sequence** *int*: sequence number of the package on its senders side of the connection
     - **ack** *int*: sequence number of the last received package from the recipients side of the connection
    A sequence of `0` means no packages have been sent or received.
    After `65535` sequence numbers wrap around to `1`, so they can be stored in 2 bytes.
     - **ack_bitfield** *str*: A 32 character string representing the 32 packages prior to `remote_sequence`,
       with the first character corresponding the packge directly preceding it and so forth.
       `'1'` means the package has been received, `'0'` means it hasn't.

    ### Optional Arguments
     - **events** *[Event]*: list of Pygase events that is to be attached to this package and sent via network

    ### Class Attributes
     - **timeout** *float*: time in seconds after which a package is considered to be lost, `1.0` by default
     - **max_size** int*: maximum size in bytes a package may have

    ### Attributes
     - **sequence** *sqn*: packages sequence number
     - **ack** *sqn*: last received remote sequence number
     - **ack_bitfield** *str*: acknowledgement status of 32 preceding remote sequence numbers as boolean bitstring
    
    ### Properties
     - **events**: iterable of **Event** objects contained in the package
    '''
    timeout = 1.0 # package timeout in seconds
    max_size = 2048 # the maximum size of Pygase package in bytes
    _protocol_id = bytes.fromhex('ffd0fab9') # unique 4 byte identifier for pygase packages

    def __init__(self, sequence:int, ack:int, ack_bitfield:str, events:list=None):
        self.sequence = sqn(sequence)
        self.ack = sqn(ack)
        self.ack_bitfield = ack_bitfield
        self._events = events if events is not None else []
        self._datagram = None

    @property
    def events(self):
        return self._events.copy()

    def add_event(self, event:Event):
        '''
        ### Arguments
         - **event** *Event*: a Pygase event that is to be attached to this package
        
        ### Raises
         - **OverflowError**: if the package had previously been converted to a datagram and
           and its size with the added event would exceed **max_size**
        '''
        if self._datagram is not None:
            bytepack = event.to_bytes()
            if len(self._datagram) + len(bytepack) + 2 > self.max_size:
                raise OverflowError('package exceeds the maximum size of ' + str(self.max_size) + ' bytes')
            self._datagram += len(bytepack).to_bytes(2, 'big') + bytepack
        self._events.append(event)

    def get_bytesize(self):
        '''
        ### Returns
        *int*: size of the package as a datagram in bytes
        '''
        if self._datagram is None:
            self._datagram = self.to_datagram()
        return len(self._datagram)

    def to_datagram(self):
        '''
        ### Returns
        *bytes*: compact bytestring representing the package, which can be sent via a datagram socket
        
        ### Raises
         - **OverflowError**: if the resulting datagram would exceed **max_size**
        '''
        if self._datagram is not None:
            return self._datagram
        datagram = bytearray(self._protocol_id)
        datagram.extend(self.sequence.to_bytes())
        datagram.extend(self.ack.to_bytes())
        datagram.extend(int(self.ack_bitfield, 2).to_bytes(4, 'big'))
        # The header makes up the first 12 bytes of the package
        for event in self._events:
            bytepack = event.to_bytes()
            datagram.extend(len(bytepack).to_bytes(2, 'big'))
            datagram.extend(bytepack)
        datagram = bytes(datagram)
        if len(datagram) > self.max_size:
            raise OverflowError('package exceeds the maximum size of ' + str(self.max_size) + ' bytes')
        self._datagram = bytes(datagram)
        return self._datagram

    @classmethod
    def from_datagram(cls, datagram:bytes):
        '''
        ### Arguments
         - **datagram** *bytes*: bytestring data, typically received via a socket
        
        ### Returns
        *Package*: the package from which the datagram has been created using `to_datagram()`

        ### Raises
         - **ProtocolIDMismatchError**: if the first four bytes don't match the Pygase protocol ID
        '''
        if datagram[:4] != cls._protocol_id:
            raise ProtocolIDMismatchError
        sequence = sqn.from_bytes(datagram[4:6])
        ack = sqn.from_bytes(datagram[6:8])
        ack_bitfield = bin(int.from_bytes(datagram[8:12], 'big'))[2:].zfill(32)
        payload = datagram[12:]
        events = []
        while len(payload) > 0:
            bytesize = int.from_bytes(payload[:2], 'big')
            events.append(Event.from_bytes(payload[2:bytesize+2]))
            payload = payload[bytesize+2:]
        result = Package(sequence, ack, ack_bitfield, events)
        result._datagram = datagram
        return result

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

class ConnectionStatus(NamedEnum): pass
ConnectionStatus.register('Disconnected')
ConnectionStatus.register('Connected')
ConnectionStatus.register('Connecting')

class Connection:
    '''
    This class resembles a client-server connection via the Pygase protocol.

    ### Arguments
     - **remote_address** *(str, int)*: A tuple `('hostname', port)` *required*
     - **event_handler**: An object that has a callable `handle()` attribute that takes
       an **Event** as argument, for example a **Pygase.event.UniversalEventHandler** instance

    ### Attributes
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
    '''

    timeout = 5.0 # connection timeout in seconds
    max_throttle_time = 60.0
    min_throttle_time = 1.0
    _package_intervals = {
        'good': 1/40,
        'bad': 1/20
    } # maps connection.quality to time between sent packages in seconds
    _latency_threshold = 0.25 # latency that will trigger connection throttling

    def __init__(self, remote_address:tuple, event_handler):
        self.remote_address = remote_address
        self.event_handler = event_handler
        self.local_sequence = sqn(0)
        self.remote_sequence = sqn(0)
        self.ack_bitfield = '0'*32
        self.latency = 0.0
        self.status = ConnectionStatus.get('Connecting')
        self.package_interval = self._package_intervals['good']
        self.quality = 'good' # this is used for congestion avoidance
        self._outgoing_event_queue = curio.UniversalQueue()
        self._incoming_event_queue = curio.UniversalQueue()
        self._pending_acks = {}
        self._event_callback_sequence = sqn(0)
        self._events_with_callbacks = {}
        self._event_callbacks = {}
        self._last_recv = time.time()

    def _update_remote_info(self, received_sequence):
        if self.remote_sequence == 0:
            self.remote_sequence = received_sequence
            return
        sequence_diff = self.remote_sequence - received_sequence
        if sequence_diff < 0:
            self.remote_sequence = received_sequence
            if sequence_diff == -1:
                self.ack_bitfield = '1' + self.ack_bitfield[:-1]
            else:
                self.ack_bitfield = self.ack_bitfield[:sequence_diff].zfill(32)
        if sequence_diff == 0:
            raise DuplicateSequenceError
        elif sequence_diff > 0:
            if self.ack_bitfield[sequence_diff-1] == '1':
                raise DuplicateSequenceError
            else:
                self.ack_bitfield = self.ack_bitfield[:sequence_diff-1] + '1' + self.ack_bitfield[sequence_diff:]

    async def _recv(self, received_package:Package):
        '''
        Updates `remote_sequence` and `ack_bitfield` based on a received package, resolves package loss
        and puts the received events in the queue of incoming events.
        
        ### Raises
         - **DuplicateSequenceError**: if a package with the same sequence has already been received
        '''
        self._last_recv = time.time()
        self._set_status('Connected')
        self._update_remote_info(received_package.sequence)
        # resolve pending acks for sent packages (NEEDS REFACTORING)
        for pending_sequence in list(self._pending_acks):
            sequence_diff = received_package.ack - pending_sequence
            if sequence_diff == 0 or (sequence_diff < 33 and received_package.ack_bitfield[sequence_diff-1] == '1'):
                self._update_latency(time.time() - self._pending_acks[pending_sequence])
                if pending_sequence in self._events_with_callbacks:
                    for event_sequence in self._events_with_callbacks[pending_sequence]:
                        if self._event_callbacks[event_sequence]['ack'] is not None:
                            self._event_callbacks[event_sequence]['ack']()
                            del self._event_callbacks[event_sequence]
                    del self._events_with_callbacks[pending_sequence]
                del self._pending_acks[pending_sequence]
            elif time.time() - self._pending_acks[pending_sequence] > Package.timeout:
                if pending_sequence in self._events_with_callbacks:
                    for event_sequence in self._events_with_callbacks[pending_sequence]:
                        if self._event_callbacks[event_sequence]['timeout'] is not None:
                            self._event_callbacks[event_sequence]['timeout']()
                            del self._event_callbacks[event_sequence]
                    del self._events_with_callbacks[pending_sequence]
                del self._pending_acks[pending_sequence]
        for event in received_package.events:
            await self._incoming_event_queue.put(event)

    def dispatch_event(self, event:Event, ack_callback=None, timeout_callback=None):
        callback_sequence = 0
        if ack_callback is not None or timeout_callback is not None:
            self._event_callback_sequence += 1
            callback_sequence = self._event_callback_sequence
            self._event_callbacks[self._event_callback_sequence] = {
                'ack': ack_callback,
                'timeout': timeout_callback
            }
        self._outgoing_event_queue.put((event, callback_sequence))

    async def _handle_next_event(self):
        event = await self._incoming_event_queue.get()
        self.event_handler.handle_blocking(event)
        await self._incoming_event_queue.task_done()

    async def _event_loop(self):
        while True:
            await self._handle_next_event()

    async def _send_loop(self, sock):
        '''
        Coroutine that, once spawned, will keep sending packages to the remote_address until it is explicitly
        cancelled or the connection times out.
        '''
        congestion_avoidance_task = await curio.spawn(self._congestion_avoidance_monitor)
        while True:
            t0 = time.time()
            if t0 - self._last_recv > self.timeout:
                self._set_status('Disconnected')
                #await self._outgoing_event_queue.put('shutdown') # should be a proper timeout event
                break
            await self._send_next_package(sock)
            await curio.sleep(max([self.package_interval - time.time() + t0, 0]))
        await congestion_avoidance_task.cancel()

    async def _send_next_package(self, sock):
        self.local_sequence += 1
        package = Package(self.local_sequence, self.remote_sequence, self.ack_bitfield)
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

    def _set_status(self, status:str):
        self.status = ConnectionStatus.get(status)

    def _update_latency(self, rtt:int):
        # smoothed moving average to filter out network jitter
        self.latency += 0.1 * (rtt - self.latency)

    async def _congestion_avoidance_monitor(self):
        state = {
            'throttle_time': self.min_throttle_time,
            'last_quality_change': time.time(),
            'last_good_quality_milestone': time.time()
        }
        while True:
            self._throttling_state_machine(time.time(), state)
            await curio.sleep(Connection.min_throttle_time/2.0)

    def _throttling_state_machine(self, t:int, state:dict):
        if self.quality == 'good':
            if self.latency > self._latency_threshold: # switch to bad mode
                self.quality = 'bad'
                self.package_interval = self._package_intervals['bad']
                # if good conditions didn't last at least the throttle time, increase it
                if t - state['last_quality_change'] < state['throttle_time']:
                    state['throttle_time'] = min([state['throttle_time']*2.0, self.max_throttle_time])
                state['last_quality_change'] = t
            # if good conditions lasted throttle time since last milestone
            elif t - state['last_good_quality_milestone'] > state['throttle_time']:
                self.package_interval = self._package_intervals['good']
                state['throttle_time'] = max([state['throttle_time']/2.0, self.min_throttle_time])
                state['last_good_quality_milestone'] = t
        else: # self.quality == 'bad'
            if self.latency < self._latency_threshold: # switch to good mode
                self.quality = 'good'
                state['last_quality_change'] = t
                state['last_good_quality_milestone'] = t

class ClientConnection(Connection):

    def __init__(self, remote_address, event_handler):
        super().__init__(remote_address, event_handler)
        self._command_queue = curio.UniversalQueue()

    def shutdown(self):
        self._command_queue.put('shutdown')

    async def loop(self):
        async with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            send_loop_task = await curio.spawn(self._send_loop, sock)
            recv_loop_task = await curio.spawn(self._client_recv_loop, sock)
            event_loop_task = await curio.spawn(self._event_loop)
            # check for disconnect event
            while True:
                command = await self._command_queue.get()
                if command == 'shutdown':
                    # this is only for testing purposes
                    await sock.sendto('shutdown'.encode('utf-8'), self.remote_address)
                    break
            await recv_loop_task.cancel()
            await send_loop_task.cancel()
            await event_loop_task.cancel()

    async def _client_recv_loop(self, sock):
        while True:
            # somehow await the first sendto call here
            data = await sock.recv(Package.max_size)
            package = Package.from_datagram(data)
            await self._recv(package)

class ServerConnection(Connection):

    @classmethod
    async def loop(cls, hostname:str, port:int, connections:dict, event_handler):
        async with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind((hostname, port))
            connection_tasks = curio.TaskGroup()
            while True:
                data, client_address = await sock.recvfrom(Package.max_size)
                try:
                    package = Package.from_datagram(data)
                    # create new connection if client is unknown
                    if not client_address in connections:
                        new_connection = cls(client_address, event_handler)
                        new_connection._set_status('Connected')
                        await connection_tasks.spawn(new_connection._send_loop, sock)
                        await connection_tasks.spawn(new_connection._event_loop)
                        connections[client_address] = new_connection
                    await connections[client_address]._recv(package)
                except ProtocolIDMismatchError:
                    # ignore all non-Pygase packages
                    pass
                # this is a rudimentary shutdown switch
                try:
                    if data.decode('utf-8') == 'shutdown':
                        break
                except UnicodeDecodeError:
                    pass
            await connection_tasks.cancel_remaining()
