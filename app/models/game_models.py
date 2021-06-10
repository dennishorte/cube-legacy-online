import json
from datetime import datetime

from sqlalchemy.dialects.mysql import MEDIUMTEXT

from app import db
from app.util.game_logic import GameState


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    state_json = db.Column(MEDIUMTEXT)

    draft_links = db.relationship('GameDraftLink', backref='game')
    draft_v2_links = db.relationship('GameDraftV2Link', backref='game')
    user_links = db.relationship('GameUserLink', backref='game')

    @staticmethod
    def active_games():
        all_games = Game.query.order_by(Game.timestamp.desc()).all()
        return [x for x in all_games if not x.state.is_finished()]

    @staticmethod
    def factory(name, players):
        game = Game()
        db.session.add(game)
        db.session.commit()

        game_state = GameState.factory(
            game_id=game.id,
            name=name
        )
        game.update(game_state)

        for player in players:
            game.add_player(player)

        return game

    def add_player(self, user):
        state = self.state
        state.add_player(user.id)

        link = GameUserLink(game_id=self.id, user_id=user.id)
        db.session.add(link)

        self.update(state)

    def add_player_by_name(self, name):
        from app.models.user_models import User

        player = User.query.filter(User.name == name).first()
        if not player:
            raise ValueError(f"Unknown player: {name}")

        self.add_player(player)

        link = GameUserLink(game_id=self.id, user_id=player.id)
        db.session.add(link)
        db.session.commit()

    def age(self):
        age = datetime.utcnow() - self.timestamp
        years = age.days // 365
        days = age.days % 365

        if years > 0:
            return f"{years} years {days} days"
        else:
            return f"{days} days"

    def is_my_turn(self, user):
        if not self.state or not self.state.player_by_id(user.id):
            return False

        if self.state.ready_to_start():
            return self.state.priority_player().name == user.name

        else:
            return not self.state.player_by_id(user.id).ready_to_start

    @property
    def state(self):
        return self.state_no_cache()

    def state_no_cache(self):
        return GameState(json.loads(self.state_json))

    def update(self, game_state):
        if hasattr(game_state, 'data'):
            game_state = game_state.data

        self.state_json = json.dumps(game_state)
        db.session.add(self)
        db.session.commit()


class GameUserLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))


class GameDraftLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))


class GameDraftV2Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey('draft_v2.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
