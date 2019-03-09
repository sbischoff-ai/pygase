# -*- coding: utf-8 -*-

from pygase.mixins import Sendable, NamedEnum

# unique 4-byte identifier for the PyGaSe package protocol
_PROTOCOL_ID = bytes.fromhex('ffd0fab9')

class ProtocolIDMismatchError(ValueError):
    pass

class DuplicateSequenceError(ConnectionError):
    pass

class Package:
    def __init__(self, sequence: int, ack: int, ack_bitfield: str, payload:bytes=None):
        self.sequence = sequence
        self.ack = ack
        self.ack_bitfield = ack_bitfield
        self.payload = payload # event protocol (contains various events + stateupdate if for client or last known state if for server)

    def to_datagram(self):
        '''
        ### Returns
          *bytes*: compact bytestring representing the package, which can be sent via a datagram socket
        '''
        datagram = bytearray(_PROTOCOL_ID)
        datagram.extend(self.sequence.to_bytes(2, 'big'))
        datagram.extend(self.ack.to_bytes(2, 'big'))
        datagram.extend(int(self.ack_bitfield, 2).to_bytes(4, 'big'))
        # The header makes up the first 12 bytes of the package
        if self.payload is not None:
            datagram.extend(self.payload)
        return bytes(datagram)

    @staticmethod
    def from_datagram(datagram: bytes):
        '''
        ### Arguments
         - **datagram** *bytes*: bytestring data, typically received via a socket
        
        ### Returns
        *Package*: the package from which the datagram has been created using `to_datagram()`

        ### Raises
         - **ProtocolIDMismatchError**: if the first four bytes don't match the Pygase protocol ID
        '''
        if datagram[:4] != _PROTOCOL_ID:
            raise ProtocolIDMismatchError
        sequence = int.from_bytes(datagram[4:6], 'big')
        ack = int.from_bytes(datagram[6:8], 'big')
        ack_bitfield = bin(int.from_bytes(datagram[8:12], 'big'))[2:].zfill(32)
        if len(datagram) > 12:
            payload = datagram[12:]
        else:
            payload = None
        return Package(sequence, ack, ack_bitfield, payload)

class ConnectionStatus(NamedEnum):
    pass
ConnectionStatus.register('Disconnected')
ConnectionStatus.register('Good')
ConnectionStatus.register('Bad') # For congestion avoidance
ConnectionStatus.register('Connecting')

class Connection:
    '''
    This class resembles a client-server connection via the Pygase protocol.

    ### Arguments
     - **remote_address** *(str, int)*: A tuple `('hostname', port)` *required*

    ### Attributes
     - **local_sequence** *int*: sequence number of the last sent package
     - **remote_sequence** *int*: sequence number of the last received package
    A sequence of `0` means no packages have been sent or received.
    After `65535` sequence numbers wrap around to `1`, so they can be stored in 2 bytes.
     - **ack_bitfield** *str*: A 32 character string representing the 32 packages prior to `remote_sequence`,
        with the first character corresponding the packge directly preceding it and so forth.
        `'1'` means the package has been received, `'0'` means it hasn't.
     - **latency**: the last registered RTT (round trip time)
     - **status** *int*: A **ConnectionStatus** value.
     - **remote_address** *(str, int)*: A tuple `('hostname', port)`
    '''
    def __init__(self, remote_address):
        self.local_sequence = 0
        self.remote_sequence = 0
        self.ack_bitfield = '0'*32
        self.latency = 0 #used for congestion avoidance, noise filtered
        self.status = ConnectionStatus.get('Connecting')
        self.remote_address = remote_address
        #self.packages_to_send
        #self.acknowledged_packages
        #self.received_package_cache
# should notify about lost packages, maybe dispatches ack and loss events?

    def update(self, received_package: Package):
        '''
        Updates `remote_sequence` and `ack_bitfield` based on a received package.
        
        ### Raises
         - **DuplicateSequenceError**: if a package with the same sequence has already been received
        '''
        if self.remote_sequence is 0:
            self.remote_sequence = received_package.sequence
            return
        sequence_diff = self.remote_sequence - received_package.sequence
        if sequence_diff < 0:
            self.remote_sequence = received_package.sequence
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

#Extra classes for servers and clients that contain the proper (non blocking) socket stuff