from app import db

from app.models.deck_models import *
from app.models.draft_models import *
from app.models.user_models import *
from app.util import card_util
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
        return iter(self.as_list())

    def __len__(self):
        return len(self.as_list())

    def as_list(self):
        filtered = []
        for wrapper in self.wrappers:
            if all([f(wrapper) for f in self.filters]):
                filtered.append(wrapper.card)

        return filtered

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

    def color(self, color_letter):
        color_letter = color_letter.upper()
        new_filter = lambda x: x.card.color_identity() == color_letter
        return self.with_filter(new_filter)

    def colorless(self):
        new_filter = lambda x: len(x.card.color_identity()) == 0
        return self.with_filter(new_filter)

    def creatures(self):
        new_filter = lambda x: x.card.is_creature()
        return self.with_filter(new_filter)

    def gold(self):
        new_filter = lambda x: len(x.card.color_identity()) > 1
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

    def card_data(self):
        data = {}
        for card in self.card_set:
            data[card.id] = card.get_json()

        return data

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
        existing_deck = self.draft.deck_for(self.user.id)

        if existing_deck:
            return existing_deck
        else:
            return self._new_deck()

    def _new_deck(self):
        deck = Deck()
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

        # Create a link between this deck and the draft
        link = DeckDraftLink()
        link.deck_id = deck.id
        link.draft_id = self.draft.id
        db.session.add(link)
        db.session.commit()

        return deck

    def _picked_cards(self):
        picked_cards = []
        for seat in self.seats:
            picked_cards += [x.cube_card for x in seat.picks]
        return picked_cards
