import random
from datetime import datetime

from app import db
from app.config import Config
from app.forms import ResultForm
from app.models.draft import *
from app.util import slack


class DraftWrapper(object):
    def __init__(self, draft_id, user):
        self.draft = Draft.query.get(draft_id)
        
        self.seats = self.draft.seats
        self.seats.sort(key=lambda x: x.order)

        self.user = user
        self.seat = next(x for x in self.seats if x.user_id == self.user.id)
        self.pack = self.seat.waiting_pack()

    def is_scarring_round(self):
        return self.pack and self.pack.is_scarring_round

    def passing_to(self):
        """User who will see this pack after you pick from it."""
        if self.pack is None:
            return None
        
        if self.pack.pack_number % 2 == 0:
            next_seat = (self.seat.order + 1) % self.draft.num_seats
        else:
            next_seat = (self.seat.order - 1) % self.draft.num_seats

        return self.seats[next_seat].user

    def pick_card(self, card_id):
        pack_card = PackCard.query.filter(PackCard.id==card_id).first()
        pack_card.picked_by_id = self.seat.id
        pack_card.pick_number = self.pack.num_picked
        pack_card.picked_at = datetime.utcnow()
        db.session.add(pack_card)
        
        self.pack.num_picked += 1
        db.session.add(self.pack)

        # If this was the last pick, mark the draft complete.
        unpicked_cards = PackCard.query.filter(
            PackCard.draft_id == self.draft.id,
            PackCard.pick_number < 0,
        ).first()
        if unpicked_cards is None:
            self.draft.complete = True
            db.session.add(self.draft)

        self.user.last_pick_timestamp = datetime.utcnow()
        db.session.add(self.user)

        # commit the update
        db.session.commit()

        if self.passing_to():
            slack.send_your_pick_notification(self.passing_to(), self.draft)

    def result_form_for(self, seat):
        result = MatchResult.query.filter(
            MatchResult.draft_id == self.draft.id,
            MatchResult.user_id == self.user.id,
            MatchResult.opponent_id == seat.user.id,
        ).first()
        
        form = ResultForm()
        form.user_id.data = seat.user.id

        if result:
            form.wins.data = result.wins
            form.losses.data = result.losses
            form.draws.data = result.draws

        return form

    def results(self, seat1, seat2):
        result = MatchResult.query.filter(
            MatchResult.draft_id == self.draft.id,
            MatchResult.user_id == seat1.user.id,
            MatchResult.opponent_id == seat2.user.id,
        ).first()

        if result:
            return f"{result.wins}-{result.losses}-{result.draws}"
        else:
            return ""
            

    ############################################################

        
    def these_scars_suck(self):
        self.unlock_new_scars()
        self._new_scars = None

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

    def has_scarred_this_round(self):
        return self._scar_that_was_applied_this_round() is not None

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
