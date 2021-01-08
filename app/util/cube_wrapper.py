import functools

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

    @functools.lru_cache
    def card_data(self):
        """
        Card json data for use in javascript (eg. legacy autocard popups)
        """
        cards = {}
        for card in self.cards(include_removed=True):
            cards[card.id] = card.get_json(add_scars=True)
        return cards

    @functools.lru_cache
    def cards(self, include_removed=False):
        """
        Get only the latest version of the cards in the cube.
        """
        if include_removed:
            cards = CubeCard.query.filter(
                CubeCard.cube_id == self.cube.id,
                CubeCard.latest == True,
            ).all()
        else:
            cards = CubeCard.query.filter(
                CubeCard.cube_id == self.cube.id,
                CubeCard.latest == True,
                CubeCard.removed_by_id == None,
            ).all()

        cards.sort(key=lambda x: x.name())
        return cards
