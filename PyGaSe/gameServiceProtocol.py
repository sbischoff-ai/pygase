# -*- coding: utf-8 -*-
'''
Module that defines the network protocol which *GameServiceConnection*s and *GamerService*s use
to communicate. It contains the *_GameServicePackage* class, which represents a unit of information
that client and server can exchange with each other, as well as classes that make up parts
of a package.
'''

import sys
from _typeclass import TypeClass
from sharedGameData import Sendable, SharedGameState, SharedGameStateUpdate, ClientActivity
# SharedGameState is not used explicitely, but it needs to be findable
# via 'getattr()' in '_GameServicePackage.from_datagram()'!

# Unique 4-byte token to mark the end of the header of a _GameServicePackage
_HEADER_END_TOKEN = bytes.fromhex('b5968459')

class PackageType(TypeClass):
    '''
    Enum class with the following values:
    - *GetSharedGameStateRequest*: As client request the full shared game state from the server.
        body = None
    - *GetGameStateUpdateRequest*: As client request all polled game state updates.
        body = *SharedGameStateUpdate* (purely for time-ordering)
    - *PostClientActivityRequest*: As client post client-side activity to the *GameService*.
        body = *ClientActivity*
    - *GameServiceResponse*: As server respond to a client request.
        body = request-dependent
    - *GameServiceError*: As server report an error to the client.
        body = *ErrorMessage*
    '''

    GetSharedGameStateRequest = 1
    GetGameStateUpdateRequest = 2
    PostClientActivityRequest = 3
    GameServiceResponse = 4
    GameServiceError = 5

    _counter = 6

class ErrorType(TypeClass):
    '''
    Enum class with the following values:
    - *RequestTimeout*: Server _response took to long.
    - *UnpackError*: Request or _response bytepack corrupted.
    - *RequestInvalid*: Server could not handle the request.

    To be used as part of an *ErrorMessage* object in a *GameServiceError* package.
    '''

    RequestTimeout = 1
    UnpackError = 2
    RequestInvalid = 3

    _counter = 4

class ErrorMessage(Sendable):
    '''
    The sendable type *ErrorMessage* is used for the body of *_GameServicePackage*s with
    *package_type* *PackageType.GameServiceError* in their *header*.
    '''
    def __init__(self, error_type=ErrorType.RequestInvalid, message=''):
        self.error_type = error_type
        self.message = message

class _GameServicePackageHeader(Sendable):
    def __init__(self, package_type=PackageType.GameServiceResponse, body_type='NoneType'):
        self.package_type = package_type
        self.body_type = body_type

    '''
    Override 'object' members
    '''
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.package_type == other.package_type and self.body_type == other.body_type
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

class _GameServicePackage:
    '''
    Contains *header* and *body* as attributes. The header contains information about the the
    package type and body. The body is some object of a core class like *ErrorMessage*,
    *SharedGameState*, *SharedGameStateUpdate* or *ClientActivity*.
    '''
    def __init__(self, package_type: PackageType, body: Sendable = None):
        self.header = _GameServicePackageHeader(package_type, body.__class__.__name__)
        self.body = body

    def to_datagram(self):
        '''
        Returns a bytepacked datagram representing the _GameServicePackage.
        '''
        self.header.body_type = self.body.__class__.__name__
        datagram = bytearray(self.header.to_bytes())
        datagram.extend(_HEADER_END_TOKEN)
        if self.body != None:
            datagram.extend(self.body.to_bytes())
        return bytes(datagram)

    @staticmethod
    def from_datagram(datagram: bytes):
        '''
        Unpacks the given bytepacked datagram and returns it's content as a *_GameServicePackage*
        object.
        '''
        datagram = datagram.split(_HEADER_END_TOKEN)
        header = _GameServicePackageHeader.from_bytes(datagram[0])
        if header.body_type != 'NoneType':
            body = getattr(sys.modules[__name__], header.body_type).from_bytes(datagram[1])
        else:
            body = None
        return _GameServicePackage(header.package_type, body)

    def is_response(self):
        '''
        Returns *True* if the package is of package type *GameServiceResponse*.
        '''
        return self.header.package_type == PackageType.GameServiceResponse

    def is_error(self):
        '''
        Returns *True* if the package is of package type *GameServiceError*.
        '''
        return self.header.package_type == PackageType.GameServiceError

    def is_update_request(self):
        '''
        Returns *True* if the package is of package type *GetGameStateUpdateRequest*.
        '''
        return self.header.package_type == PackageType.GetGameStateUpdateRequest

    def is_state_request(self):
        '''
        Returns *True* if the package is of package type *GetSharedGameStateRequest*.
        '''
        return self.header.package_type == PackageType.GetSharedGameStateRequest

    def is_post_activity_request(self):
        '''
        Returns *True* if the package is of package type *PostClientActivityRequest*.
        '''
        return self.header.package_type == PackageType.PostClientActivityRequest

    '''
    Override object members
    '''
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.header == other.header and self.body == other.body
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

def _timeout_error(message=''):
    '''
    Returns a *_GameServicePackage* with package type *GameServiceError*,
    error type *RequestTimeout* and *message* as error message.
    '''
    return _GameServicePackage(
        package_type=PackageType.GameServiceError,
        body=ErrorMessage(
            error_type=ErrorType.RequestTimeout,
            message=message
        )
    )

def _unpack_error(message=''):
    '''
    Returns a *_GameServicePackage* with package type *GameServiceError*,
    error type *UnpackError* and *message* as error message.
    '''
    return _GameServicePackage(
        package_type=PackageType.GameServiceError,
        body=ErrorMessage(
            error_type=ErrorType.UnpackError,
            message=message
        )
    )

def _request_invalid_error(message=''):
    '''
    Returns a *_GameServicePackage* with package type *GameServiceError*,
    error type *RequestInvalid* and *message* as error message.
    '''
    return _GameServicePackage(
        package_type=PackageType.GameServiceError,
        body=ErrorMessage(
            error_type=ErrorType.RequestInvalid,
            message=message
        )
    )

def _game_state_request():
    '''
    Returns a *_GameServicePackage* with package type *GetSharedGameStateRequest*.
    '''
    return _GameServicePackage(
        package_type=PackageType.GetSharedGameStateRequest
    )

def _game_state_update_request(time_order: int):
    '''
    Returns a *_GameServicePackage* with package type *GetGameStateUpdateRequest*.
    Enter the *time_order* attribute of the client's last known *SharedGameState*.
    '''
    return _GameServicePackage(
        package_type=PackageType.GetGameStateUpdateRequest,
        body=SharedGameStateUpdate(
            time_order=time_order
        )
    )

def _post_activity_request(client_activity: ClientActivity):
    '''
    Returns a *_GameServicePackage* with package type *PostClientActivityRequest* with
    the given *ClientActivity* object as it's body.
    '''
    return _GameServicePackage(
        package_type=PackageType.PostClientActivityRequest,
        body=client_activity
    )

def _response(body: Sendable):
    '''
    Returns a *_GameServicePackage* with package type *GameServiceResponse*.
    '''
    return _GameServicePackage(
        package_type=PackageType.GameServiceResponse,
        body=body
    )
