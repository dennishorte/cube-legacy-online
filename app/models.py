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
    added_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    image_url = db.Column(db.String(511))

    picks = db.relationship('PackCard', backref='card')
    scars = db.relationship('Scar', backref='card')

    def __repr__(self):
        return '<Card {}:{}>'.format(self.name, self.id)

    def image_urls(self):
        return self.image_url.split(',')


class Scar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime,
        index=True,
        default=datetime.utcnow,
        comment="Time this scar was added to the pool",
    )
    card_id = db.Column(
        db.Integer,
        db.ForeignKey('card.id'),
        comment="Card this scar is applied to. If null, not yet applied.",
    )
    added_by_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        comment="User who added this scar to a card.",
    )
    added_timestamp = db.Column(
        db.DateTime,
        comment="Time this scar was applied to a card.",
    )
    text=db.Column(
        db.String(256),
        comment="Text that will be added to the card this scar is applied to.",
    )
    restrictions=db.Column(
        db.String(64),
        default='',
        comment="Limitations on the kind of card this scar can be applied to.",
    )
    reminder=db.Column(
        db.String(256),
        default='',
        comment="Some additional explanation of what this scar does.",
    )
    notes_id=db.Column(
        db.String(256),
        default='',
        comment="Thoughts the player had when adding this scar to the card.",
    )

    def __repr__(self):
        return '<Scar {}>'.format(self.id)

    
class Draft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    complete = db.Column(db.Boolean)
    pack_size = db.Column(db.Integer)
    num_packs = db.Column(db.Integer)
    num_seats = db.Column(db.Integer)
    scar_rounds_str = db.Column(db.String(64))  # eg. "1,4"

    packs = db.relationship('Pack', backref='draft')
    pack_cards = db.relationship('PackCard', backref='draft')
    participants = db.relationship('Participant', backref='draft')

    def __repr__(self):
        return '<Draft {}>'.format(self.name)

    def scar_rounds(self):
        return [int(x) for x in self.scar_rounds_str]

    def scar_map(self):
        """
        A map of pack_card.id -> [Scar models] for all cards in this draft.
        """
        card_ids = [x.card_id for x in self.pack_cards]
        scars = Scar.query.filter(Scar.card_id.in_(card_ids)).all()
        scar_map = {}
        for scar in scars:
            scar_map.setdefault(scar.card_id, []).append(scar)
        return scar_map


class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'))
    seat = db.Column(db.Integer)
    
    picks = db.relationship('PackCard', backref='picked_by')

    def __repr__(self):
        return '<Participant {}>'.format(self.user.username)

    def waiting_packs(self):
        """
        Return all packs that this participant is blocking.
        """
        num_seats = self.draft.num_seats
        last_pick = len(self.picks)

        packs = []
        while True:
            next_pick = last_pick + 1
            
            next_pack = last_pick // self.draft.pack_size
            next_pick_for_pack = last_pick % self.draft.pack_size + 1

            if next_pack % 2 == 0:  # Pass left
                next_seat = (num_seats + self.seat - (next_pick_for_pack - 1)) % num_seats
                
            else:  # pass right
                next_seat = (self.seat + next_pick_for_pack - 1) % num_seats

            pack = Pack.query.filter(
                Pack.draft_id == self.draft_id,
                Pack.seat_number == next_seat,
                Pack.pack_number == next_pack,
                Pack.num_picked == next_pick_for_pack - 1,
            ).first()

            if pack is None:
                break
            else:
                packs.append(pack)
                last_pick += 1

        return packs

    def waiting_pack(self):
        """
        Return the next pack this player should draft, if any.
        """
        waiting = self.waiting_packs()
        if waiting:
            return waiting[0]
        else:
            return None
        

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

    def pick_number(self):
        return self.num_picked + 1

    def complete(self):
        return self.num_picked == self.draft.pack_size


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


class ScryfallData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(127), index=True)
    json = db.Column(db.String(16383))
