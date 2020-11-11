from app import db

from app.models.deck import *
from app.models.draft import *
from app.models.user import *


class CardSet(object):
    def __init__(self, cards, filters=[]):
        self.cards = cards
        self.cards.sort(key=lambda x: x.name())

        self.filters = filters

    def __iter__(self):
        filtered = []
        for card in self.cards:
            if all([f(card) for f in self.filters]):
                filtered.append(card)

        return iter(filtered)

    def cmc(self, cmc):
        new_filter = lambda x: x.cmc() == cmc
        return self.with_filter(new_filter)

    def cmc_gte(self, cmc):
        new_filter = lambda x: x.cmc() >= cmc
        return self.with_filter(new_filter)

    def cmc_lte(self, cmc):
        new_filter = lambda x: x.cmc() <= cmc
        return self.with_filter(new_filter)

    def creatures(self):
        new_filter = lambda x: x.is_creature()
        return self.with_filter(new_filter)

    def land(self):
        new_filter = lambda x: x.is_land()
        return self.with_filter(new_filter)

    def non_creature(self):
        new_filter = lambda x: not x.is_creature()
        return self.with_filter(new_filter)

    def other(self):
        new_filter = lambda x: not x.is_land() and not x.is_creature()
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

        self.deck = self._load_deck()

        self.card_set = CardSet([])
        for card in self.deck.maindeck():
            card.sideboard = False
            self.card_set.cards.append(card)

        for card in self.deck.sideboard():
            card.sideboard = True
            self.card_set.cards.append(card)

    def basics(self, name):
        if not self.deck.basic_lands:
            return '0'

        for elem in self.deck.basic_lands.split(','):
            tokens = elem.split()
            if len(tokens) == 2 and tokens[1] == name:
                return tokens[0]
        return '0'

    def _load_deck(self):
        existing_deck = Deck.query.filter(
            Deck.draft_id == self.draft.id,
            Deck.user_id == self.user.id,
        ).first()

        if existing_deck:
            return self._add_latest_picks(existing_deck)

        else:
            return self._new_deck()

    def _add_latest_picks(self, deck):
        deck_cards = deck.maindeck() + deck.sideboard()
        if len(deck_cards) == len(self.seat.picks):
            return deck

        else:
            for card in self.seat.picks:
                if card.cube_card not in deck_cards:
                    deck.add_card(card.cube_card)
                    print(f"Adding {card.cube_card.name()}")

            db.session.add(deck)
            db.session.commit()

            return deck

    def _new_deck(self):
        deck = Deck()
        deck.draft_id = self.draft.id
        deck.user_id = self.user.id
        deck.name = f"{self.user.name}'s {self.draft.name} Deck"

        maindeck = []
        sideboard = []
        for card in self.seat.picks:
            if card.sideboard:
                sideboard.append(card.cube_card)
            else:
                maindeck.append(card.cube_card)

        deck.set_maindeck(maindeck)
        deck.set_sideboard(sideboard)

        db.session.add(deck)
        db.session.commit()

        return deck
