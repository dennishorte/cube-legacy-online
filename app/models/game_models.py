import functools
import json
from datetime import datetime

from sqlalchemy.dialects.mysql import MEDIUMTEXT

from app import db
from app.util.game_logic import GameState


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    state_json = db.Column(MEDIUMTEXT)

    def is_my_turn(self, user):
        return self.state.priority_player().name == user.name

    @functools.cached_property
    def state(self):
        return GameState(json.loads(self.state_json))

    def update(self, game_state):
        if hasattr(game_state, 'data'):
            game_state = game_state.data

        self.state_json = json.dumps(game_state)
        db.session.add(self)
        db.session.commit()
