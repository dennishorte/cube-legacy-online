from datetime import datetime

from app import db
from app.models.cube import CubeCard


class Deck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'))

    name = db.Column(db.String(64))

    # Format is comma-separated CubeCard ids.
    maindeck_ids = db.Column(db.Text, default='')
    sideboard_ids = db.Column(db.Text, default='')

    # Format is "5 Mountain,3 Island"
    basic_lands = db.Column(db.Text, default='')

    def add_card(self, card):
        self.maindeck_ids += ',' + str(card.id)

    def maindeck(self):
        ids = [int(x) for x in self.maindeck_ids.split(',') if x]
        card_map = {x.id: x for x in CubeCard.query.filter(CubeCard.id.in_(ids)).all()}
        print(ids)
        print(card_map)
        return [card_map[x] for x in ids]

    def sideboard(self):
        ids = [int(x) for x in self.sideboard_ids.split(',') if x]
        card_map = {x.id: x for x in CubeCard.query.filter(CubeCard.id.in_(ids)).all()}
        return [card_map[x] for x in ids]

    def set_maindeck(self, cards: list):
        self.maindeck_ids = self._card_list_to_comma_separated(cards)

    def set_sideboard(self, cards: list):
        self.sideboard_ids = self._card_list_to_comma_separated(cards)

    def _card_list_to_comma_separated(self, cards: list):
        cube_cards = []
        for card in cards:
            if isinstance(card, CubeCard):
                cube_cards.append(card)
            elif hasattr(card, 'cube_card'):
                cube_cards.append(card.cube_card)
            else:
                raise ValueError(f"Unknown card type: {card}")

        return ','.join([str(x.id) for x in cube_cards])
