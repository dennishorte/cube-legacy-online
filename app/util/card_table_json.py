import re

from app.util.card_util import CardConsts
from app.util.card_util import cmc_from_string
from app.util.card_util import color_sort_key
from app.util.cube_wrapper import CubeWrapper
from app.util.enum import Layout


class CardColumnSection(object):
    def __init__(self, header, cards):
        self.header = header
        self.cards = cards

    def sort_cards_by_cmc(self):
        self.cards.sort(key=lambda x: (x.cmc(), x.name()))

        if self.cards:
            self.cards[0].section_divider = 'table-section-divider'

        for i in range(1, len(self.cards)):
            if self.cards[i-1].cmc() < self.cards[i].cmc():
                self.cards[i].section_divider = 'table-section-divider'
            else:
                self.cards[i].section_divider = ''

    def num_cards(self):
        return len(self.cards)


class CardColumn(object):
    def __init__(self, header, color):
        self.header = header
        self.color_class = color
        self.sections = []

    def num_cards(self):
        return sum([x.num_cards() for x in self.sections])


class CardTableJson(object):
    HEADERS = [
        'White',
        'Blue',
        'Black',
        'Red',
        'Green',
        'Gold',
        'Colorless',
        'Land',
    ]

    def __init__(self, card_data):
        self.card_data = card_data
        self.columns = []

        self._init_columns()

    def _init_columns(self):
        divided_cards = self._divide_cards_by_column()

        for header in self.HEADERS:
            column = CardColumn(header, header.lower())

            if header == 'Gold':
                # column.sections = [CardColumnSection('Cards', divided_cards[header])]
                column.sections = self._divide_gold_by_guild(divided_cards[header])
            else:
                column.sections = self._divide_cards_by_type(divided_cards[header])

            for section in column.sections:
                section.sort_cards_by_cmc()
            self.columns.append(column)

    def _divide_gold_by_guild(self, cards):
        guilds = {x: [] for x in CardConsts.MULTICOLOR_MAP}

        for card in cards:
            identity = card.color_identity().upper()
            identity = ''.join(sorted(identity))
            guilds[identity].append(card)

        sections = []
        for identity, cards in guilds.items():
            sections.append(CardColumnSection(
                identity,
                cards,
            ))
        sections.sort(key=lambda x: (len(x.header), CardConsts.MULTICOLOR_MAP[x.header]))
        for section in sections:
            section.header = CardConsts.MULTICOLOR_MAP[section.header]

        return sections


    def _divide_cards_by_type(self, cards):
        types = {x: [] for x in CardConsts.CARD_TYPES}

        for card in cards:
            for type in CardConsts.CARD_TYPES:
                if card.has_type(type):
                    types[type].append(card)
                    break
            else:
                types['other'].append(card)

        sections = []
        for type, cards in types.items():
            sections.append(CardColumnSection(type.title(), cards))

        return sections

    def _divide_cards_by_column(self):
        columns = {x: [] for x in self.HEADERS}

        for card_id, card_json in self.card_data.items():
            card_json['cube_card_id'] = int(card_id)
            card_wrapper = JsonCardWrapper(card_json)
            if card_wrapper.color_identity() == 'W':
                columns['White'].append(card_wrapper)
            elif card_wrapper.color_identity() == 'U':
                columns['Blue'].append(card_wrapper)
            elif card_wrapper.color_identity() == 'B':
                columns['Black'].append(card_wrapper)
            elif card_wrapper.color_identity() == 'R':
                columns['Red'].append(card_wrapper)
            elif card_wrapper.color_identity() == 'G':
                columns['Green'].append(card_wrapper)
            elif len(card_wrapper.color_identity()) > 1:
                columns['Gold'].append(card_wrapper)
            elif card_wrapper.is_land():
                columns['Land'].append(card_wrapper)
            elif card_wrapper.color_identity() == '':
                columns['Colorless'].append(card_wrapper)
            else:
                raise ValueError(f"Unknown card type for card: {card_wrapper.name()}")

        return columns


class JsonCardWrapper(object):
    def __init__(self, card_json):
        self.data = card_json

    def card_face(self, index):
        faces = self.card_faces()
        if len(faces) <= index:
            return None
        else:
            return faces[index]

    def card_faces(self):
        return self.data['card_faces']

    def cmc(self):
        cost = 0
        cost += cmc_from_string(self.card_faces()[0]['mana_cost'])

        if self.layout() == Layout.split.name:
            cost += cmc_from_string(self.card_faces()[1]['mana_cost'])

        return cost

    def color_identity(self):
        pattern = r"{(.*?)}"
        identity = set()
        for face in self.card_faces():
            texts = [face['mana_cost']] + re.findall(pattern, face['oracle_text'])
            for text in texts:
                for ch in face['mana_cost'].upper():
                    if ch in 'WUBRG':
                        identity.add(ch)

        identity = sorted(identity, key=color_sort_key)
        identity = ''.join(identity)

        return identity

    def has_type(self, card_type):
        return card_type.lower() in self.card_faces()[0].get('type_line', '').lower()

    def id(self):
        return self.data['cube_card_id']

    def image_back(self):
        images = self.image_urls()
        if len(images) > 1:
            return images[1]

    def image_front(self):
        return self.image_urls()[0]

    def image_urls(self):
        data = self.data
        layout = data['layout']
        if Layout.simple_faced_layout(layout) or Layout.split_faced_layout(layout):
            return [data['card_faces'][0]['image_url']]
        elif Layout.double_sided_layout(layout):
            return [x['image_url'] for x in self.card_faces() if 'image_url' in x]
        else:
            raise ValueError(f"Unknown layout type: {layout}")

    def is_scarred(self):
        return any([x.get('scarred') for x in self.card_faces()])

    def layout(self):
        return self.data['layout']

    def linked_achievements(self):
        return self.card_faces()[0].get('achievements', [])

    def name(self):
        return self.data['name']

    def is_creature(self):
        return 'creature' in self.card_faces()[0].get('type_line', '').lower()

    def is_land(self):
        return 'land' in self.card_faces()[0].get('type_line', '').lower()

    def oracle_text(self):
        return self.data['oracle_text']

    def rarity(self):
        return self.data['rarity']

    def type_line(self):
        return self.data.get('type_line', 'NO_TYPE')
