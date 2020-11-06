from app import db

from app.models.draft import *
from app.models.user import *


class CardSet(object):
    def __init__(self, cards, filters=[]):
        self.cards = cards
        self.cards.sort(key=lambda x: x.cube_card.name())

        self.filters = filters

    def __iter__(self):
        filtered = []
        for card in self.cards:
            if all([f(card) for f in self.filters]):
                filtered.append(card)

        return iter(filtered)

    def cmc(self, cmc):
        new_filter = lambda x: x.cube_card.cmc() == cmc
        return self.with_filter(new_filter)

    def cmc_gte(self, cmc):
        new_filter = lambda x: x.cube_card.cmc() >= cmc
        return self.with_filter(new_filter)

    def cmc_lte(self, cmc):
        new_filter = lambda x: x.cube_card.cmc() <= cmc
        return self.with_filter(new_filter)

    def creatures(self):
        new_filter = lambda x: x.cube_card.is_creature()
        return self.with_filter(new_filter)

    def land(self):
        new_filter = lambda x: x.cube_card.is_land()
        return self.with_filter(new_filter)

    def non_creature(self):
        new_filter = lambda x: not x.cube_card.is_creature()
        return self.with_filter(new_filter)

    def other(self):
        new_filter = lambda x: not x.cube_card.is_land() and not x.cube_card.is_creature()
        return self.with_filter(new_filter)

    def maindeck(self):
        new_filter = lambda x: not x.sideboard
        return self.with_filter(new_filter)

    def sideboard(self):
        new_filter = lambda x: x.sideboard
        return self.with_filter(new_filter)

    def with_filter(self, f):
        return CardSet(self.cards, self.filters + [f])


class DeckBuilder(object):
    def __init__(self, draft_id, user_id):
        self.draft = Draft.query.get(draft_id)
        self.user = User.query.get(user_id)
            
        self.seat = Seat.query.filter(
            Seat.draft_id == self.draft.id,
            Seat.user_id == self.user.id,
        ).first()

        self.pack_cards = self.seat.picks
        self.cards = [x.cube_card for x in self.pack_cards]

        self.card_set = CardSet(self.pack_cards)

    def save_deck(self, data: dict):
        if not self.deck:
            self.deck = DeckListV2()
            self.deck.draft_id = self.draft.id
            self.deck.user_id = self.user.id

        self.deck.name = data['name']
        self.deck.maindeck_ids = data['maindeck_ids']
        self.deck.sideboard_ids = data['sideboard_ids']

        db.session.add(self.deck)
        db.session.commit()
