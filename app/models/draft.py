from datetime import datetime

from app import db
from app.models.cube import *
from app.models.user import *


class Draft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    name = db.Column(db.String(64))

    complete = db.Column(db.Boolean)

    # Setup info
    pack_size = db.Column(db.Integer)
    num_packs = db.Column(db.Integer)
    num_seats = db.Column(db.Integer)
    scar_rounds_str = db.Column(db.String(64))  # eg. "1,4"

    # Relationships
    seats = db.relationship('Seat', backref='draft')
    packs = db.relationship('Pack', backref='draft')
    pack_cards = db.relationship('PackCard', backref='draft')

    def __repr__(self):
        return '<Draft {}>'.format(self.name)

    def scar_rounds(self):
        return [int(x) for x in self.scar_rounds_str.split(',')]

    # def scar_map(self):
    #     """
    #     A map of pack_card.id -> [Scar models] for all cards in this draft.
    #     """
    #     card_ids = [x.card_id for x in self.pack_cards]
    #     scars = Scar.query.filter(Scar.card_id.in_(card_ids)).all()
    #     scar_map = {}
    #     for scar in scars:
    #         scar_map.setdefault(scar.card_id, []).append(scar)
    #     return scar_map


class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'))

    # Relationships
    picks = db.relationship('PackCard', backref='picked_by')

    def __repr__(self):
        return '<Seat {}>'.format(self.user.username)

    def waiting_packs(self):
        """
        Return all packs that this seat is blocking.
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

    def num_picked_for_round(self, pack_index):
        all_picks = PackCard.query.filter(
            PackCard.draft_id == self.draft_id,
            PackCard.picked_by_id == self.id
        ).all()

        round_to_picks = {}
        for pick in all_picks:
            round = pick.pack.pack_number
            round_to_picks.setdefault(round, []).append(pick)

        return len(round_to_picks.get(pack_index, []))
        

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

    def seat_ordering(self):
        pack_size = self.draft.pack_size
        num_seats = self.draft.num_seats
        
        seat_range = range(pack_size)
        if self.direction() == 'right':
            seat_range = [0 - x for x in seat_range]
        
        return [(x + self.seat_number) % num_seats for x in seat_range]

    def next_seat(self):
        return self.seat_ordering[self.num_picked]

    def pick_number(self):
        return self.num_picked + 1

    def complete(self):
        return self.num_picked == self.draft.pack_size


class PackCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cube_card.id'))
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'))
    pack_id = db.Column(db.Integer, db.ForeignKey('pack.id'))
    picked_by_id = db.Column(db.Integer, db.ForeignKey('seat.id'))
    pick_number = db.Column(db.Integer, default=-1)
    picked_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<PackCard {}>'.format(self.card.name)
    
    def picked(self):
        return self.pick_number > -1
    
