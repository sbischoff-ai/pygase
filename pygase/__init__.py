# -*- coding: utf-8 -*-
"""Create smooth and scalable online and LAN multiplayer games easily.

PyGaSe, or Python Game Server, is a library (or framework, whichever term you prefer) that provides
a complete set of high-level components for real-time networking for games.

As a user of this library you will only need classes and functions directly imported from `pygase`:

```python
# For clients:
from pygase import Client

# For backends:
from pygase import GameState, GameStateStore, GameStateMachine, Server
# Not necessary but might come in handy:
from pygase import get_availabe_ip_addresses
```

"""

from pygase.client import Client as Client
from pygase.backend import Backend as Backend, Server as Server, GameStateStore as GameStateStore, GameStateMachine as GameStateMachine
from pygase.gamestate import GameState as GameState
from pygase.utils import get_available_ip_addresses as get_available_ip_addresses

__all__ = [
    "Backend",
    "Client",
    "GameState",
    "GameStateMachine",
    "GameStateStore",
    "Server",
    "get_available_ip_addresses",
]
