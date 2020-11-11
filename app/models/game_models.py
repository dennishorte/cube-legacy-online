import functools
import json
from datetime import datetime

from app import db
from app.util.game_logic import GameState


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    state_json = db.Column(db.Text)

    @functools.cached_property
    def state(self):
        return GameState(json.loads(self.state_json))

    def update(self, game_state):
        self.state_json = json.dumps(game_state.data)
        db.session.add(self)
        db.session.commit()
