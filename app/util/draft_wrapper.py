import random
from datetime import datetime

from app import db
from app.config import Config
from app.forms import ResultForm
from app.models.draft_models import *
from app.util import slack
from app.util.deck_builder import DeckBuilder
from app.util.enum import DraftFaceUp
from app.util.cube_wrapper import CubeWrapper


class DraftWrapper(object):
    def __init__(self, draft_id, user):
        self.draft = Draft.query.get(draft_id)
        self.cube = self.draft.cube
        self.cube_wrapper = CubeWrapper(self.cube)

        self.seats = self.draft.seats
        self.seats.sort(key=lambda x: x.order)

        self.user = user
        self.seat = next(x for x in self.seats if x.user_id == self.user.id)
        self.pack = self.seat.waiting_pack()

        self.decklist = DeckList.query.filter(
            DeckList.draft_id == self.draft.id,
            DeckList.user_id == self.user.id,
        ).first()

        self.deck_builder = DeckBuilder(self.draft.id, self.user.id)

    def card_data(self):
        pack_cards = PackCard.query.filter(PackCard.draft_id == self.draft.id).all()
        cube_cards = [x.cube_card for x in pack_cards]
        return {x.id: x.get_json() for x in cube_cards}

    def face_up_cards(self):
        cards = PackCard.query.filter(
            PackCard.draft_id == self.draft.id,
            PackCard.faceup == True,
        ).all()

        if not cards:
            return None

        by_seat = {}
        for card in cards:
            by_seat.setdefault(card.picked_by, []).append(card)

        return by_seat

    def picks_creatures(self):
        return [x for x in self.seat.picks if not x.sideboard and x.cube_card.is_creature()]

    def picks_non_creatures(self):
        return [x for x in self.seat.picks if not x.sideboard and not x.cube_card.is_creature()]

    def picks_sideboard(self):
        return [x for x in self.seat.picks if x.sideboard]

    def is_scarring_round(self):
        return self.pack and self.pack.is_scarring_round()

    def passing_to(self):
        """User who will see this pack after you pick from it."""

        return self.passing_to_seat().user

    def passing_to_seat(self):
        if self.pack is None:
            return None

        if self.pack.pack_number % 2 == 0:
            next_seat = (self.seat.order + 1) % self.draft.num_seats
        else:
            next_seat = (self.seat.order - 1) % self.draft.num_seats

        return self.seats[next_seat]

    def pick_card(self, card_id, face_up=DraftFaceUp.false):
        pack_card = PackCard.query.filter(PackCard.id==card_id).first()

        if not self.pack:
            raise ValueError(f"No pack to pick from right now.")

        if not pack_card.pack_id == self.pack.id:
            raise ValueError(f"{card_id}: {card.cube_card.name()} is not part of pack {self.pack.id}. It's in pack {card.pack_id}.")

        if face_up == DraftFaceUp.optional:
            raise ValueError("Can't choose optional for draft face up. Please specify t or f")

        # If the card was drafted face up.
        if face_up == DraftFaceUp.true \
           or pack_card.cube_card.draft_face_up() == DraftFaceUp.true:
            pack_card.faceup = True
            message = Message()
            message.draft_id = self.draft.id
            message.text = f"{self.user.name} drafted {pack_card.cube_card.name()} face up."
            db.session.add(message)

        pack_card.picked_by_id = self.seat.id
        pack_card.pick_number = self.pack.num_picked
        pack_card.picked_at = datetime.utcnow()
        db.session.add(pack_card)

        self.pack.num_picked_tmp += 1
        self.draft.num_picked_tmp += 1
        db.session.add(self.pack)
        db.session.add(self.draft)

        self.user.last_pick_timestamp = datetime.utcnow()
        db.session.add(self.user)

        # commit the update
        db.session.commit()

        next_seat = self.passing_to_seat()
        if next_seat and next_seat.waiting_pack():
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
