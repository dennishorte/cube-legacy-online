from app import db

from app.models.deck_models import *
from app.models.draft_models import *
from app.models.user_models import *
from app.util.cube_wrapper import CubeWrapper


class CardWrapper(object):
    """Required in order to ensure that duplicate cards can have different metadata
    """
    def __init__(self, card):
        self.card = card
        self.maindeck = False
        self.sideboard = False
        self.command = False


class CardSet(object):
    def __init__(self):
        self.wrappers = []
        self.filters = []

    def __iter__(self):
        filtered = []
        for wrapper in self.wrappers:
            if all([f(wrapper) for f in self.filters]):
                filtered.append(wrapper.card)

        return iter(filtered)

    def add_card(self, card, maindeck=False, sideboard=False, command=False):
        card = CardWrapper(card)
        card.maindeck = maindeck
        card.sideboard = sideboard
        card.command = command
        self.wrappers.append(card)

    def cmc(self, cmc):
        new_filter = lambda x: x.card.cmc() == cmc
        return self.with_filter(new_filter)

    def cmc_gte(self, cmc):
        new_filter = lambda x: x.card.cmc() >= cmc
        return self.with_filter(new_filter)

    def cmc_lte(self, cmc):
        new_filter = lambda x: x.card.cmc() <= cmc
        return self.with_filter(new_filter)

    def creatures(self):
        new_filter = lambda x: x.card.is_creature()
        return self.with_filter(new_filter)

    def land(self):
        new_filter = lambda x: x.card.is_land()
        return self.with_filter(new_filter)

    def non_creature(self):
        new_filter = lambda x: not x.card.is_creature()
        return self.with_filter(new_filter)

    def other(self):
        new_filter = lambda x: not x.card.is_land() and not x.card.is_creature()
        return self.with_filter(new_filter)

    def command(self):
        new_filter = lambda x: x.command
        return self.with_filter(new_filter)

    def maindeck(self):
        new_filter = lambda x: x.maindeck
        return self.with_filter(new_filter)

    def sideboard(self):
        new_filter = lambda x: x.sideboard
        return self.with_filter(new_filter)

    def with_filter(self, f):
        updated = CardSet()
        updated.wrappers = self.wrappers
        updated.filters = self.filters + [f]
        return updated


class DeckBuilder(object):
    def __init__(self, draft_id, user_id):
        draft = Draft.query.get(draft_id)
        if draft.parent_id:
            self.draft = Draft.query.get(draft.parent_id)
        else:
            self.draft = draft
        self.draft_ids = [self.draft.id] + [x.id for x in self.draft.children()]

        self.cube = self.draft.cube
        self.cube_wrapper = CubeWrapper(self.cube)

        self.user = User.query.get(user_id)

        self.seats = Seat.query.filter(
            Seat.draft_id.in_(self.draft_ids),
            Seat.user_id == self.user.id,
        ).all()

        self.deck = self._load_deck()

        self.card_set = CardSet()
        for card in self.deck.maindeck():
            self.card_set.add_card(card, maindeck=True)

        for card in self.deck.sideboard():
            self.card_set.add_card(card, sideboard=True)

        for card in self.deck.command():
            self.card_set.add_card(card, command=True)

    def all_cards(self):
        cards = []

        drafts = Draft.query.filter(Draft.id.in_(self.draft_ids)).all()
        for draft in drafts:
            cards += self.cube_wrapper.cards(include_removed=True)

        return list(set(cards))

    def basics(self, name):
        if not self.deck.basic_lands:
            return '0'

        for elem in self.deck.basic_lands.split(','):
            tokens = elem.split()
            if len(tokens) == 2 and tokens[1] == name:
                return tokens[0]
        return '0'

    def deck_list(self, legacy_names=False):
        """
        Return a decklist formatted to be used by Cockatrice and other systems.
        """
        cards = []

        for card in self.deck.maindeck():
            if legacy_names:
                cards.append(card.cockatrice_name())
            else:
                cards.append(card.name())

        for basic in [x.strip() for x in self.deck.basic_lands.split(',') if x.strip()]:
            if legacy_names:
                cards.append(basic + "'")
            else:
                cards.append(basic)

        cards.append('\u00a0')  # Non-breaking space

        for card in self.deck.sideboard() + self.deck.command():
            if legacy_names:
                cards.append(card.cockatrice_name())
            else:
                cards.append(card.name())

        return cards

    def is_legacy(self):
        return self.draft.cube.style_a == 'legacy'

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
        deck_cards = deck.all_cards()
        picked_cards = self._picked_cards()

        if len(deck_cards) == len(picked_cards):
            return deck

        # Record how many of each card is currently in the deck.
        deck_counts = {}
        for card in deck_cards:
            if card.id not in deck_counts:
                deck_counts[card.id] = 1
            else:
                deck_counts[card.id] += 1

        # Count down using the picked cards, and any time you'd go below zero, add it to the deck
        to_add = []
        for card in picked_cards:
            if card.id not in deck_counts or deck_counts[card.id] == 0:
                to_add.append(card)
            else:
                deck_counts[card.id] -= 1

        # Add in all the cards that have been picked but were not present in the deck.
        if to_add:
            for card in to_add:
                deck.add_card(card)

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
        for card in self._picked_cards():
            if card.sideboard:
                sideboard.append(card.cube_card)
            else:
                maindeck.append(card.cube_card)

        deck.set_maindeck(maindeck)
        deck.set_sideboard(sideboard)

        db.session.add(deck)
        db.session.commit()

        return deck

    def _picked_cards(self):
        picked_cards = []
        for seat in self.seats:
            picked_cards += [x.cube_card for x in seat.picks]
        return picked_cards
