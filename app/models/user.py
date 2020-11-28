from flask_login import current_user
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from app import db
from app import login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    slack_id = db.Column(db.String(50))

    last_pick_timestamp = db.Column(db.DateTime)
    last_notif_timestamp = db.Column(db.DateTime)

    monikers_tsv = db.Column(db.Text)

    cubes = db.relationship('Cube', backref='created_by')
    draft_seats = db.relationship('Seat', backref='user')
    match_results = db.relationship('MatchResult', backref='user')

    cards_added = db.relationship('CubeCard', backref='added_by', foreign_keys='CubeCard.added_by_id')
    cards_edited = db.relationship('CubeCard', backref='edited_by', foreign_keys='CubeCard.edited_by_id')
    cards_removed = db.relationship('CubeCard', backref='removed_by', foreign_keys='CubeCard.removed_by_id')

    scars_created = db.relationship('Scar', backref='created_by', foreign_keys='Scar.created_by_id')
    scars_added = db.relationship('Scar', backref='applied_by', foreign_keys='Scar.applied_by_id')
    scars_removed = db.relationship('Scar', backref='removed_by', foreign_keys='Scar.removed_by_id')

    achievements_created = db.relationship('Achievement', backref='created_by', foreign_keys='Achievement.created_by_id')
    achievements_unlocked = db.relationship('Achievement', backref='unlocked_by', foreign_keys='Achievement.unlocked_by_id')

    achievements_starred = db.relationship('AchievementStar', backref='user')

    decks = db.relationship('Deck', backref='user')

    def __repr__(self):
        return '<User {}>'.format(self.name)

    @staticmethod
    def all_names():
        return [x.name for x in User.query.order_by(User.name)]

    def active_draft_seats(self):
        active_seats = [
            x for x in self.draft_seats
            if not x.draft.complete and not x.draft.killed
        ]
        active_seats.sort(key=lambda x: x.draft.timestamp, reverse=True)
        return active_seats

    def active_games(self):
        return [x for x in self.all_games() if not x.state.is_finished()]

    def all_games(self):
        from app.models.game_models import Game
        return [
            x for x in Game.query.order_by(Game.timestamp.desc()).all()
            if x.state.player_by_id(current_user.id)
        ]

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def monikers(self):
        if self.monikers_tsv:
            return self.monikers_tsv.split('\t')
        else:
            return []

    def set_monikers(self, monikers: list):
        self.monikers_tsv = '\t'.join(monikers)
        db.session.add(self)
        db.session.commit()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def should_send_notification(self):
        return (
            not self.last_notif_timestamp
            or not self.last_pick_timestamp
            or self.last_notif_timestamp < self.last_pick_timestamp
        )

    def waiting_drafts(self):
        active = self.active_draft_seats()
        return [x for x in active if x.waiting_pack()]

    def waiting_games(self):
        active = self.active_games()
        return [x for x in active if x.state.priority_player().name == self.name]


@login.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()
