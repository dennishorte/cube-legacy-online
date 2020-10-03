from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from app import db
from app import login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    slack_id = db.Column(db.String(50))
    
    cards_added = db.relationship('Card', backref='added_by')
    scars_applied = db.relationship('Scar', backref='added_by')
    participations = db.relationship('Participant', backref='user')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)    


@login.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    added_by_id= db.Column(db.Integer, db.ForeignKey('user.id'))

    picks = db.relationship('PackCard', backref='card')
    scars = db.relationship('Scar', backref='card')

    def __repr__(self):
        return '<Card {}:{}>'.format(self.name, self.id)


class Scar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'))
    added_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    text=db.Column(db.String(256))

    def __repr__(self):
        return '<Scar {}>'.format(self.id)

    
class Draft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    complete = db.Column(db.Boolean)
    pack_size = db.Column(db.Integer)
    num_packs = db.Column(db.Integer)
    num_seats = db.Column(db.Integer)

    packs = db.relationship('Pack', backref='draft')
    pack_cards = db.relationship('PackCard', backref='draft')
    participants = db.relationship('Participant', backref='draft')

    def __repr__(self):
        return '<Draft {}>'.format(self.name)


class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'))
    seat = db.Column(db.Integer)
    
    picks = db.relationship('PackCard', backref='picked_by')

    def __repr__(self):
        return '<Participant {}>'.format(self.user.username)

    def waiting_pack(self):
        """
        Return the next pack this player should draft, if any.
        """
        all_packs = self.draft.packs
        waiting = [x for x in all_packs if x.next_seat() == self.seat]
        waiting.sort(key=self._pack_sort_key)

        if waiting and self._ready_to_pick(waiting[0]):
            return waiting[0]
        else:
            return None

    @staticmethod
    def _pack_sort_key(pack):
        return (pack.pack_number, pack.num_picked)

    def _ready_to_pick(self, pack):
        """
        A player can only pick from the next round if they have enough picks already for
        the current round.
        """
        num_packs_completed = len(self.picks) // self.draft.pack_size
        return pack.pack_number <= num_packs_completed


class Pack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'))
    seat_number = db.Column(db.Integer)
    pack_number = db.Column(db.Integer)
    num_picked = db.Column(db.Integer, default=0)

    cards = db.relationship('PackCard', backref='pack')

    def __repr__(self):
        return '<Pack s:{} p:{} n:{}>'.format(self.seat_number, self.pack_number, self.num_picked)

    def direction(self):
        if self.pack_number % 2 == 0:
            return 'left'    # Meaning if this is seat number 2, it will pass to seat 3.
        else:
            return 'right'

    def next_seat(self):
        num_seats = self.draft.num_seats

        tmp = self.seat_number + num_seats * 100
        if self.direction() == 'left':
            tmp += self.num_picked
        else:
            tmp -= self.num_picked

        return tmp % num_seats


class PackCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'))
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'))
    pack_id = db.Column(db.Integer, db.ForeignKey('pack.id'))
    picked_by_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    pick_number = db.Column(db.Integer, default=-1)

    def __repr__(self):
        return '<PackCard {}>'.format(self.card.name)
    
    def picked(self):
        return self.pick_number > -1
