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


class GameResults(object):
    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.in_progress = 0

    def add_result(self, result: str):
        if result == 'win':
            self.wins += 1
        elif result == 'loss':
            self.losses += 1
        elif result == 'draw':
            self.draws += 1
        elif result == 'in_progress':
            self.in_progress += 1
        else:
            raise ValueError(f"Unknown result: {result}")

    def count(self):
        return self.wins + self.losses

    def win_loss_str(self):
        if self.wins + self.losses + self.draws + self.in_progress == 0:
            return ''
        else:
            return f"{self.wins}-{self.losses}"

    def __str__(self):
        return f"{self.wins}-{self.losses}-{self.draws}-{self.in_progress}"



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

        self.deck_builder = DeckBuilder(self.draft.id, self.user.id)

        self.results_dict = self._game_results_linked()

    def card_data(self):
        pack_cards = PackCard.query.filter(PackCard.draft_id == self.draft.id).all()
        cube_cards = [x.cube_card for x in pack_cards]
        base_set = {x.id: x.get_json() for x in cube_cards}
        base_set.update(self.deck_builder.card_data())
        return base_set

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

    def pick_card(self, card_id):
        pack_card = PackCard.query.filter(PackCard.id==card_id).first()

        if not self.pack:
            raise ValueError(f"No pack to pick from right now.")

        if not pack_card.pack_id == self.pack.id:
            raise ValueError(f"{card_id}: {card.cube_card.name()} is not part of pack {self.pack.id}. It's in pack {card.pack_id}.")

        # If the card was drafted face up.
        if pack_card.cube_card.draft_face_up() == DraftFaceUp.true:
            pack_card.faceup = True
            message = Message()
            message.draft_id = self.draft.id
            message.text = f"{self.user.name} drafted {pack_card.cube_card.name()} face up."
            db.session.add(message)

        # Basic pack_card updates to indicate a card was picked.
        pack_card.picked_by_id = self.seat.id
        pack_card.pick_number = self.pack.num_picked
        pack_card.picked_at = datetime.utcnow()
        db.session.add(pack_card)

        # Update the pack and draft pick counts.
        # This is an optimization because a huge amount of time was being spent querying
        # the database for all of the picks in order to determine which pack was available
        # and if the draft was complete.
        self.pack.num_picked_tmp += 1
        self.draft.num_picked_tmp += 1
        db.session.add(self.pack)
        db.session.add(self.draft)

        # Remember last pick timestamp to determine if notifications should be sent
        # when a pack is passed.
        self.user.last_pick_timestamp = datetime.utcnow()
        db.session.add(self.user)

        # Add the card to the deck
        self.deck_builder.deck.add_card(pack_card.cube_card)
        db.session.add(self.deck_builder.deck)

        # commit the update
        db.session.commit()

        # update pick info for card
        pack_card.cube_card.pick_info_update()

        next_seat = self.passing_to_seat()
        if next_seat and next_seat.waiting_pack():
            slack.send_your_pick_notification(self.passing_to(), self.draft)

    def result_form_for(self, opp_seat):
        results = self.results(self.user.id, opp_seat.user_id)

        form = ResultForm()
        form.user_id.data = opp_seat.user_id
        form.wins.data = results.wins
        form.losses.data = results.losses
        form.draws.data = results.draws

        return form

    def results(self, user_id1, user_id2):
        # Manually entered match results
        result = MatchResult.query.filter(
            MatchResult.draft_id == self.draft.id,
            MatchResult.user_id == user_id1,
            MatchResult.opponent_id == user_id2,
        ).first()

        if result:
            r = GameResults()
            r.wins = result.wins
            r.losses = result.losses
            r.draws = result.draws
            return r
        else:
            return self.results_dict.get(user_id1, {}).get(user_id2, GameResults())


    def _game_results_linked(self):
        """
        Auto-generated match results from linked games
        """

        from app.models.game_models import GameDraftLink

        game_links = GameDraftLink.query.filter(GameDraftLink.draft_id == self.draft.id).all()
        all_games = [x.game for x in game_links]

        results_map = {}

        for game in all_games:
            all_users = [x.user_id for x in game.user_links]
            for user_id in all_users:
                user_results = results_map.setdefault(user_id, {})
                for opp_id in all_users:
                    if user_id == opp_id:
                        continue

                    match_results = user_results.setdefault(opp_id, GameResults())
                    match_results.add_result(game.state.result_for(user_id))

        return results_map
