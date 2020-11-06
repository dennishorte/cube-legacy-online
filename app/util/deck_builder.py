from app import db

from app.models.draft import *
from app.models.user import *


class CardSet(object):
    def __init__(self, cards):
        self.cards = cards
        self.cards.sort(key=lambda x: x.cube_card.name())

    def cmc(self, cmc):
        return CardSet([x for x in self.cards if x.cube_card.cmc() == cmc])

    def cmc_gte(self, cmc):
        return CardSet([x for x in self.cards if x.cube_card.cmc() >= cmc])

    def cmc_lte(self, cmc):
        return CardSet([x for x in self.cards if x.cube_card.cmc() <= cmc])

    def creatures(self):
        return CardSet([x for x in self.cards if x.cube_card.is_creature()])

    def land(self):
        return CardSet([x for x in self.cards if x.cube_card.is_land()])

    def other(self):
        return CardSet([x for x in self.cards if not x.cube_card.is_land() and not x.cube_card.is_creature()])

    def maindeck(self):
        return CardSet([x for x in self.cards if not x.sideboard])

    def sideboard(self):
        return CardSet([x for x in self.cards if x.sideboard])


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
