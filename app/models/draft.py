import functools
from datetime import datetime

from app import db
from app.models.cube import *
from app.models.deck import *
from app.models.user import *


class Draft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    name = db.Column(db.String(64))
    killed = db.Column(db.Boolean, default=False)

    # Setup info
    pack_size = db.Column(db.Integer)
    num_packs = db.Column(db.Integer)
    num_seats = db.Column(db.Integer)
    scar_rounds_str = db.Column(db.String(64), default="")  # eg. "1,4"

    # Foreign Keys
    cube_id = db.Column(db.Integer, db.ForeignKey('cube.id'))

    # Relationships
    seats = db.relationship('Seat', backref='draft')
    packs = db.relationship('Pack', backref='draft')
    pack_cards = db.relationship('PackCard', backref='draft')
    match_results = db.relationship('MatchResult', backref='draft')
    messages = db.relationship('Message', backref='draft')
    decks = db.relationship('Deck', backref='draft')
    ach_links = db.relationship('AchievementDraftLink', backref='draft')

    def __repr__(self):
        return '<Draft {}>'.format(self.name)

    @functools.cached_property
    def complete(self):
        unpicked_cards = PackCard.query.filter(
            PackCard.draft_id == self.id,
            PackCard.pick_number == -1,
        ).first()
        return unpicked_cards is None

    def scar_rounds(self):
        return [int(x) for x in self.scar_rounds_str.split(',') if x.strip()]

    def match_record(self, user_id):
        wins = 0
        losses = 0
        draws = 0

        for result in self.match_results:
            if result.user_id == user_id:
                if result.wins > result.losses:
                    wins += 1
                elif result.wins < result.losses:
                    losses += 1
                else:
                    draws += 1

        return f"{wins}-{losses}-{draws}"

    def achs(self, user_id):
        return [x for x in self.ach_links if x.ach.unlocked_by_id == user_id]


class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'))

    # Relationships
    picks = db.relationship('PackCard', backref='picked_by')

    def __repr__(self):
        return '<Seat {}>'.format(self.user.name)

    def waiting_packs(self):
        """
        Return all packs that this seat is blocking.
        """
        # Collect all packs that it is my pick for and sort by pick order.
        packs = self.draft.packs
        up_for_me = [x for x in packs if x.next_seat and x.next_seat.id == self.id]
        up_for_me.sort(key=lambda x: (x.pack_number * 100) + x.num_picked)

        # Remove packs that I can't pick from right now.
        can_pick_now = []
        my_total_picks = len(self.picks)
        for pack in up_for_me:
            if pack.total_pick_number() == my_total_picks + 1:
                can_pick_now.append(pack)
                my_total_picks += 1

        return can_pick_now

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

    def unlock_scars(self, commit=True):
        pack = self.waiting_pack()
        if not pack:
            return

        for pack_scar in Scar.get_for_pack(pack.id, self.user.id):
            pack_scar.unlock(commit=False)
            db.session.add(pack_scar)

        if commit:
            db.session.commit()


class Pack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'))
    seat_number = db.Column(db.Integer)
    pack_number = db.Column(db.Integer)
    scarred_this_round_id = db.Column(db.Integer)  # CubeCard id

    cards = db.relationship('PackCard', backref='pack')

    def __repr__(self):
        return '<Pack s:{} p:{} n:{}>'.format(self.seat_number, self.pack_number, self.num_picked)

    def can_be_drafted(self, pack_card):
        """False if the user just scarred this card or it has already been picked."""
        return (
            self.can_be_seen(pack_card)           # Is possible to see the card at all
            and not self.just_scarred(pack_card)  # Not just scarred by current drafter
            and pack_card.pick_number == -1       # Not picked yet
            and not self.is_scarring_round        # Already placed scar, if scarring round
        )

    def can_be_seen(self, pack_card):
        """False if card was picked before the first time the player saw this pack."""
        first_saw = self.seat_ordering().index(self.next_seat_order())
        return pack_card.pick_number == -1 or first_saw <= pack_card.pick_number

    def direction(self):
        if self.pack_number % 2 == 0:
            return 'left'    # Meaning if this is seat number 2, it will pass to seat 3.
        else:
            return 'right'

    @functools.cached_property
    def is_scarring_round(self):
        return (
            self.num_picked == 0  # first pick of round
            and self.scarred_this_round_id is None
            and self.pack_number in self.draft.scar_rounds()
        )

    def just_scarred(self, pack_card):
        return self.num_picked == 0 and self.scarred_this_round_id == pack_card.cube_card.id

    def next_seat_order(self):
        if self.num_picked < len(self.seat_ordering()):
            return self.seat_ordering()[self.num_picked]
        else:
            return None

    @functools.cached_property
    def next_seat(self):
        return Seat.query.filter(
            Seat.draft_id == self.draft_id,
            Seat.order == self.next_seat_order()
        ).first()

    @functools.cached_property
    def num_picked(self):
        return len(self.picked_cards())

    def pick_number(self):
        return self.total_pick_number() % self.draft.pack_size

    def total_pick_number(self):
        return (self.pack_number * self.draft.pack_size) + self.num_picked + 1

    def complete(self):
        return self.num_picked == self.draft.pack_size

    @functools.lru_cache
    def picked_cards(self):
        picked = [x for x in self.cards if x.pick_number != -1]
        picked.sort(key=lambda x: x.pick_number)
        return picked

    def scar_options(self):
        if not self.is_scarring_round:
            return None

        user = self.next_seat.user
        choices = Scar.get_for_pack(self.id, user.id)

        if not choices:
            choices = Scar.lock_random_scars(self.id, user.id, 2)

        choices.sort(key=lambda x: x.id)

        return choices

    def seat_ordering(self):
        pack_size = self.draft.pack_size
        num_seats = self.draft.num_seats

        seat_range = range(pack_size)
        if self.direction() == 'right':
            seat_range = [0 - x for x in seat_range]

        return [(x + self.seat_number) % num_seats for x in seat_range]

    def unpicked_cards(self):
        return [x for x in self.cards if x.pick_number == -1]


class PackCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cube_card.id'))
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'))
    pack_id = db.Column(db.Integer, db.ForeignKey('pack.id'))
    picked_by_id = db.Column(db.Integer, db.ForeignKey('seat.id'))
    pick_number = db.Column(db.Integer, default=-1)
    picked_at = db.Column(db.DateTime)

    # When a card is drafted face up, this is true. It can be swapped to false if the
    # conditions of the card are met.
    faceup = db.Column(db.Boolean, default=False)

    # During a draft, players can mark cards for their sideboard
    sideboard = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<PackCard {}>'.format(self.cube_card.name())

    def picked(self):
        return self.pick_number > -1


class MatchResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    opponent_id = db.Column(db.Integer, index=True, nullable=False)
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'), nullable=False)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<MatchResult {self.user_id} vs {self.opponent_id} {self.wins}-{self.losses}-{self.draws}>"

    def get_or_create_inverse(self):
        result = MatchResult.query.filter(
            MatchResult.draft_id == self.draft_id,
            MatchResult.user_id == self.opponent_id,
            MatchResult.opponent_id == self.user_id,
        ).first()

        if not result:
            result = MatchResult()
            result.user_id=self.opponent_id
            result.opponent_id=self.user_id
            result.draft_id=self.draft_id

        result.wins=self.losses
        result.losses=self.wins
        result.draws=self.draws

        return result


class DeckList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'), nullable=False)
    name = db.Column(db.String(128))
    decklist = db.Column(db.Text)

    def mainboard(self):
        return self._split_decklist_on_empty_line()[0]

    def sideboard(self):
        return self._split_decklist_on_empty_line()[1]

    def _split_decklist_on_empty_line(self):
        card_names = self.decklist.split('\n')
        empty_index = card_names.index('')

        if empty_index > 0:
            return card_names[:empty_index], card_names[empty_index+1:]

        else:
            return card_names, []


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    text = db.Column(db.Text)


class AchievementDraftLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'), nullable=False)
    ach_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
