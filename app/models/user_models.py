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

    is_admin = db.Column(db.Boolean, default=False)

    last_pick_timestamp = db.Column(db.DateTime)
    last_notif_timestamp = db.Column(db.DateTime)

    # Stats
    monikers_tsv = db.Column(db.Text)
    personas_tsv = db.Column(db.Text)
    portrait_link = db.Column(db.Text)
    xp = db.Column(db.Integer, default=0)

    # Relationships
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

    levelup_claims = db.relationship('LevelupClaim', backref='user')

    game_links = db.relationship('GameUserLink', backref='user')

    def __repr__(self):
        return '<User {}>'.format(self.name)

    @staticmethod
    def all_names():
        return [x.name for x in User.query.order_by(User.name)]

    def active_games(self):
        return [x for x in self.all_games() if not x.state.is_finished()]

    def all_games(self):
        from app.models.game_models import Game
        from app.models.game_models import GameUserLink

        game_ids = [x.game_id for x in GameUserLink.query.filter(GameUserLink.user_id == self.id).all()]
        return Game.query.filter(Game.id.in_(game_ids)).order_by(Game.timestamp.desc()).all()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def draft_v1_seats(self):
        return self.draft_seats

    def drafts(self):
        from app.models.draft_v2_models import DraftStates
        from app.models.draft_v2_models import DraftV2
        from app.models.draft_v2_models import DraftUserLink

        links = DraftUserLink.query.filter(DraftUserLink.user_id == self.id).all()
        draft_ids = [x.draft_id for x in links]
        return DraftV2.query \
                      .filter(DraftV2.id.in_(draft_ids)) \
                      .order_by(DraftV2.timestamp.desc()) \
                      .all()

    def drafts_complete(self):
        from app.models.draft_v2_models import DraftStates
        return [x for x in self.drafts() if x.state == DraftStates.COMPLETE]

    def drafts_incomplete(self):
        from app.models.draft_v2_models import DraftStates
        return [x for x in self.drafts() if x.state in (DraftStates.SETUP, DraftStates.ACTIVE)]

    def drafts_waiting(self):
        return [x for x in self.drafts_incomplete() if x.info().waiting(self)]

    @property
    def monikers(self):
        if self.monikers_tsv:
            return self.monikers_tsv.split('\t')
        else:
            return []

    @property
    def personas(self):
        if self.personas_tsv:
            return self.personas_tsv.split('\t')
        else:
            return []

    def set_monikers(self, monikers: list):
        self.monikers_tsv = '\t'.join(monikers)
        db.session.add(self)
        db.session.commit()

    def set_personas(self, personas: list):
        self.personas_tsv = '\t'.join(personas)
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

    def waiting_games(self, exclude_id=None):
        if isinstance(exclude_id, str):
            exclude_id = int(exclude_id)

        return [
            x for x in self.active_games()
            if x.is_my_turn(self)
            and x.id != exclude_id
        ]


class Levelup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    xp = db.Column(db.Integer, nullable=False)
    reward = db.Column(db.Text, nullable=False)

    claims = db.relationship('LevelupClaim', backref='levelup')

    def claim_for(self, user_id):
        return LevelupClaim.query.filter(
            LevelupClaim.levelup_id == self.id,
            LevelupClaim.user_id == user_id,
        ).first()

    def reward_paragraphs(self):
        return [x.strip() for x in self.reward.split('\n') if x.strip()]


class LevelupClaim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    levelup_id = db.Column(db.Integer, db.ForeignKey('levelup.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    story = db.Column(db.Text)


@login.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()
