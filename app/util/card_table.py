from app.util.card_util import CardConsts


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


class CardTable(object):
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

    def __init__(self, cube):
        self.cube = cube
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

        for card in self.cube.cards():
            if card.color_identity() == 'W':
                columns['White'].append(card)
            elif card.color_identity() == 'U':
                columns['Blue'].append(card)
            elif card.color_identity() == 'B':
                columns['Black'].append(card)
            elif card.color_identity() == 'R':
                columns['Red'].append(card)
            elif card.color_identity() == 'G':
                columns['Green'].append(card)
            elif len(card.color_identity()) > 1:
                columns['Gold'].append(card)
            elif card.is_land():
                columns['Land'].append(card)
            elif card.color_identity() == '':
                columns['Colorless'].append(card)
            else:
                raise ValueError(f"Unknown card type for card: {card.name()}")

        return columns
