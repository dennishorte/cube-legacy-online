import random

from app import db
from app.models import *


class DraftWrapper(object):
    def __init__(self, draft_id, user):
        self.draft = Draft.query.get(draft_id)
        self.user = user
        self.participant = next(x for x in self.draft.participants if x.user_id == user.id)
        self.pack = self.participant.waiting_pack()
        self.picks = PackCard.query.filter(
            PackCard.draft_id==draft_id,
            PackCard.picked_by_id==self.participant.id,
        ).all()
        self.seating = self.draft.participants
        self.seating.sort(key=lambda x: x.seat)
        self.scar_map = self.draft.scar_map()

        self._new_scars = None
        self._pack_cards = None

    def _scar_that_was_applied_this_round(self):
        return Scar.query.filter(
            Scar.draft_id == self.draft.id,
            Scar.draft_pack_number == self.pack.pack_number,
            Scar.added_by_id == self.user.id
        ).first()

    def _player_scarred_card_just_now(self, card):
        scar = self._scar_that_was_applied_this_round()
        return (
            scar is not None
            and scar.card_id == card.id
        )

    def _player_can_pick_pack_card(self, pack_card):
        return (
            not pack_card.picked()
            and not self._player_scarred_card_just_now(pack_card.card)
        )

    def pack_cards(self):
        if self.pack is None:
            return None
        
        if self._pack_cards is None:
            self._pack_cards = [x for x in self.pack.cards if self._player_can_pick_pack_card(x)]

        return self._pack_cards

    def is_scarring_round(self):
        return (
            len(self.pack_cards()) == self.draft.pack_size  # first pick of round
            and self.pack.pack_number in self.draft.scar_rounds()
            and not self.has_scarred_this_round()
        )

    def has_scarred_this_round(self):
        return self._scar_that_was_applied_this_round() is not None

    def get_new_scars(self):
        # Use cached scars, if available.
        if self._new_scars:
            return self._new_scars
        
        # See if there are already some scars locked for this player for this draft.
        locked = Scar.get_locked(self.draft.id, self.participant.id)
        if locked:
            self._new_scars = locked
            return self._new_scars

        # Generate some new scars for this player.
        unused = Scar.query.filter(Scar.added_timestamp == None).all()
        random.shuffle(unused)
        self._new_scars = unused[:2]
        
        for scar in self._new_scars:
            scar.lock(self.draft.id, self.participant.id)
            db.session.add(scar)
        db.session.commit()
        return self._new_scars

    def unlock_new_scars(self):
        scars = self.get_new_scars()
        for s in scars:
            s.unlock()
            db.session.add(s)
        db.session.commit()
    
    def apply_scar(self, card_id, scar_id):
        Scar.apply_to_card(
            card_id=card_id,
            scar_id=scar_id,
            user_id=self.user.id,
            draft_id=self.draft.id,
            pack_number=self.pack.pack_number,
        )
        self.unlock_new_scars()
        # All the calls in this function commit the changes to the db on their own.
        # So, no commit here.
        self._new_scars = None
    
    def pick_card(self, card_id):
        pack_card = PackCard.query.filter(PackCard.id==card_id).first()
        pack_card.picked_by = self.participant
        pack_card.pick_number = self.pack.num_picked + 1
        db.session.add(pack_card)
        
        self.pack.num_picked += 1
        db.session.add(self.pack)

        # If this was the last pick, mark the draft complete.
        if self.pack.num_picked == self.draft.pack_size \
                and self.pack.pack_number == self.draft.num_packs - 1:
            unpicked_cards = PackCard.query.filter(
                PackCard.draft_id == self.draft.id,
                PackCard.pick_number < 0,
            ).first()
            if unpicked_cards is None:
                self.draft.complete = True
                db.session.add(self.draft)

        # commit the update
        db.session.commit()

    def passing_to(self):
        """Name of the player who will see this pack after you pick from it."""
        if self.pack is None:
            return None
        
        if self.pack.pack_number % 2 == 0:
            next_seat = (self.participant.seat + 1) % self.draft.num_seats
        else:
            next_seat = (self.participant.seat - 1) % self.draft.num_seats

        return self.seating[next_seat].user.username


def create_draft(
        name: str,
        participants: list,  # List of usernames
        pack_size: int,
        num_packs: int,
        scarring_rounds: list,  # List of ints, 0 indexed
):
    draft = Draft(
        name=name,
        complete=False,
        pack_size=pack_size,
        num_packs=num_packs,
        num_seats=len(participants),
        scar_rounds_str=','.join([str(x) for x in scarring_rounds]),
    )
    db.session.add(draft)

    random.shuffle(participants)
    for seat, p in enumerate(participants):
        user = User.query.filter(User.username==p).first()
        p_orm = Participant(
            user=user,
            draft=draft,
            seat=seat,
        )
        db.session.add(p_orm)

    for i, pack in enumerate(_make_packs(pack_size, num_packs, len(participants))):
        pack_number = i % num_packs
        seat_number = i // num_packs
        
        pack_orm = Pack(
            draft=draft,
            seat_number=seat_number,
            pack_number=pack_number,
        )
        db.session.add(pack_orm)

        for card in pack:
            pc = PackCard(
                card=card,
                draft=draft,
                pack=pack_orm,
            )
            db.session.add(card)
        
    db.session.commit()


def _make_packs(pack_size, num_packs, num_players):
    cards = Card.query.all()
    total_cards = pack_size * num_packs * num_players
    total_packs = num_packs * num_players

    if len(cards) < total_cards:
        raise ValueError("Not enough cards ({}) for {} packs of size {} and {} players.".format(
            len(cards), num_packs, pack_size, num_players))

    random.shuffle(cards)
    cards = cards[:total_cards]
    packs = []
    for i in range(total_packs):
        start = i * pack_size
        end = start + pack_size
        packs.append(cards[start:end])

    return packs  # List of list of Card ORMs
