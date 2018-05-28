# -*- coding: utf-8 -*-
'''
This module contains classes for game objects that are relevant for both client and server.
Client as well as server are supposed to define subclasses of the classes in this module,
that extend those types with data and functionality, that is client-/server-specific.
'''

import umsgpack
from _typeclass import TypeClass

class Sendable:
    '''
    Mixin for classes that are supposed to be sendable as part of a server request or response.
    Sendables can only have basic Python types as attributes and their constructor needs
    to be callable without passing any arguments.
    '''

    def to_bytes(self):
        '''
        Packs and return a small a binary representation of self.

        '''
        return umsgpack.packb(self.__dict__)

    @classmethod
    def from_bytes(cls, bytepack: bytes):
        '''
        Returns a copy of the object that was packed into byte format.
        '''
        try:
            received_sendable = cls()
            received_sendable.__dict__ = umsgpack.unpackb(bytepack)
            return received_sendable
        except KeyError:
            raise TypeError('Bytes could no be parsed into ' + cls.__name__ + '.')

class GameStatus(TypeClass):
    '''
    Enum class with the values:
    - *Paused*
    - *Active*
    '''
    Paused = 1
    Active = 2

    _counter = 3

class ActivityType(TypeClass):
    '''
    Enum class with the values:
    - *PauseGame*
    - *ResumeGame*
    '''

    PauseGame = 1
    ResumeGame = 2
    JoinServer = 3
    
    _counter = 4

    

class SharedGameState(Sendable):
    '''
    Contains game state information that is required to be known both by the server and the client.
    Since it is a *Sendable*, it can only contain basic python types as attributes.

    *time_order* should be in alignment with the servers current update counter.
    '''

    def __init__(self, time_order=0, game_status=GameStatus().Paused):
        self.game_status = game_status
        self.time_order = time_order
        self.players = {}

        ### ONLY FOR TESTING PURPOSES
        self.test_pos = 0

    def is_paused(self):
        '''
        Returns *True* if game status is *Paused*.
        '''
        return self.game_status == GameStatus().Paused

    '''
    Overrides of 'object' member functions
    '''
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.game_status == other.game_status
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

class SharedGameStateUpdate(Sendable):
    '''
    Represents a set of changes to carry out on a *SharedGameState*.
    The server should keep an update counter and label all updated with ascending index.

    Keywords are *SharedGameState* atttribute names.

    Use the *+* operator to add *SharedGameStateUpdate*s together or to add them to a
    *SharedGameState* (returning the updated update/state).

    Adding up available updates will always result in an equally or more current but
    also heavier update (meaning it will contain more data).
    '''

    def __init__(self, time_order=0, **kwargs):
        self.__dict__ = kwargs
        self.time_order = time_order

    # Adding to another update should return an updated update
    def __add__(self, other):
        if other > self:
            self.__dict__.update(other.__dict__)
            return self
        else:
            other.__dict__.update(self.__dict__)
            return other

    # Adding to a SharedGameState should update and return the state
    def __radd__(self, other):
        if type(other) is int:
            # This is so that sum() works on lists of updates, because
            # sum will always begin by adding the first element of the
            # list to 0.
            return self
        if self.time_order > other.time_order:
            other.__dict__.update(self.__dict__)
        return other

    # Check time ordering
    def __lt__(self, other):
        return self.time_order < other.time_order

    def __gt__(self, other):
        return self.time_order > other.time_order

class ClientActivity(Sendable):
    '''
    An update the client sends to the server about client-side processes like player movement and
    collisions. The server will validate *ClientActivity* samples and respond with an *OutOfSync*
    error, if they contradict the server-side game state.

    *activity_data* is a *dict* object, that contains all necessary information to process the
    activity server-side (a player's *id*, *position* and *velocity* for example).
    '''
    def __init__(self, activity_type=ActivityType.PauseGame, activity_data={}):
        self.activity_type = activity_type
        self.activity_data = activity_data

def join_server_activity(player_name: str):
    '''
    Returns a *ClientActivity* that joins a player with name *player_name* to the game.
    '''
    return ClientActivity(
        activity_type=ActivityType.JoinServer,
        activity_data={'name': player_name}
    )

def toggle_pause_activity(shared_game_state: SharedGameState):
    '''
    Returns a *ClientActivity* that either pauses or resumes the server's game loop, depending
    on the *game_status* of the given *SharedGameState*.
    '''
    if shared_game_state.is_paused():
        activity_type = ActivityType.ResumeGame
    else:
        activity_type = ActivityType.PauseGame
    return ClientActivity(
        activity_type=activity_type,
        activity_data={}
    )
