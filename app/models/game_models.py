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
        from app.util.game_logic import GamePhase

        if not self.state or not self.state.player_by_id(user.id):
            return False

        return (
            self.state.phase == GamePhase.deck_selection
            and not self.state.player_by_id(user.id).has_deck()
        ) or (
            self.state.phase != GamePhase.deck_selection
            and self.state.priority_player().name == user.name
        )

    @functools.cached_property
    def state(self):
        return GameState(json.loads(self.state_json))

    def update(self, game_state):
        if hasattr(game_state, 'data'):
            game_state = game_state.data

        self.state_json = json.dumps(game_state)
        db.session.add(self)
        db.session.commit()
