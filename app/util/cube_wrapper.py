from app.models.cube_models import Cube
from app.models.cube_models import CubeCard


class CubeWrapper(object):
    def __init__(self, cube):
        if isinstance(cube, int) or isinstance(cube, str):
            self.cube = Cube.query.get(cube)
        elif isinstance(cube, Cube):
            self.cube = cube
        else:
            raise ValueError(f"Unknown cube type: {cube}")

        self._cards = None
        self._cards_include_removed = None
        self._card_set = None

    def card_data(self):
        """
        Card json data for use in javascript (eg. legacy autocard popups)
        """
        cards = {}
        for card in self.cards(include_removed=True):
            cards[card.id] = card.get_json()
        return cards

    def cards(self, include_removed=False):
        """
        Get only the latest version of the cards in the cube.
        """
        if include_removed:
            if not self._cards_include_removed:
                self._cards_include_removed = CubeCard.query.filter(
                    CubeCard.cube_id == self.cube.id,
                    CubeCard.latest == True,
                ).all()
                self._cards_include_removed.sort(key=lambda x: x.name())
            return self._cards_include_removed
        else:
            if not self._cards:
                self._cards = CubeCard.query.filter(
                    CubeCard.cube_id == self.cube.id,
                    CubeCard.latest == True,
                    CubeCard.removed_by_id == None,
                ).all()
                self._cards.sort(key=lambda x: x.name())
            return self._cards

    def card_set(self):
        from app.util.deck_builder import CardSet
        if not self._card_set:
            self._card_set = CardSet()
            for card in self.cards():
                self._card_set.add_card(card)

        return self._card_set
