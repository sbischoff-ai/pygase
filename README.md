# PyGaSe
**Py**thon**Ga**me**Se**rver

A Python package that contains a high-performance, versatile UDP-based game server, client and network protocol with a simple API.

## Usage

### Server

```Python
import PyGaSe.shared
import PyGaSe.server

# Create your server-side game state object
SHARED_GAME_STATE = PyGaSe.shared.GameState()

class MyGameLoop(PyGaSe.server.GameLoop):
    # Override the handle_activity method
    def handle_activity(self, activitiy, update):
        if activity.activitiy_type == PyGaSe.shared.ActivityType.MovePlayer:
            player_id = activitiy.activity_data['player_id']
            new_position = activitiy.activity_data['new_position']
            update.players[player_id]['position'] = new_position
```

TODO
