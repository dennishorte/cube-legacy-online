from app.util.card_json_wrapper import CardJsonWrapper
from app.util.card_util import CardConsts
from app.util.cube_wrapper import CubeWrapper


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
            card_wrapper = CardJsonWrapper(card_json)
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
