import difflib


class CardConsts(object):
    ROOT_KEYS = (
        'card_faces',
        'cmc',
        'layout',
        'name',
        'object',
        'oracle_text',
        'type_line',
    )

    FACE_KEYS = (
        'flavor_text',
        'image_url',
        'loyalty',
        'mana_cost',
        'name',
        'object',
        'oracle_text',
        'power',
        'toughness',
        'type_line',
    )

    CARD_TYPES = (
        'creature',
        'planeswalker',
        'sorcery',
        'instant',
        'artifact',
        'enchantment',
        'land',
    )
        


class CardColumn(object):
    def __init__(self, name, sections):
        self.name = name
        self.sections = sections

    def num_cards(self):
        return sum([len(x.cards) for x in self.sections])


class CardColumnSection(object):
    def __init__(self, name, cards):
        self.name = name
        self.cards = cards


class CardDiffer(object):
    def __init__(self, old, new, face=None):
        self.old = old
        self.new = new
        self.face = face

        if len(self.old.card_faces()) <= face:
            self.old_face = {}
        else:
            self.old_face = self.old.card_faces()[self.face]

        if len(self.new.card_faces()) <= face:
            self.new_face = {}
        else:
            self.new_face = self.new.card_faces()[self.face]

    def __getitem__(self, key):
        return self._ndiff(key)

    def summary(self):
        base = [
            self.name(),
            self.mana_cost(),
            self.type_line(),
            self.flavor_text(),
            self.pt(),
            self.loyalty(),
            self.oracle_text(),
        ]
        flat = []
        for row in base:
            if isinstance(row, list):
                flat += row
            else:
                flat.append(row)

        return [x for x in flat if x]

    def name(self):
        return self._simple_diff('name', 'name')

    def mana_cost(self):
        return self._simple_diff('mana_cost', 'cost')

    def type_line(self):
        return self._simple_diff('type_line', 'type')

    def oracle_text(self):
        diff = list(difflib.ndiff(
            self.old_face.get('oracle_text', '').split('\n'),
            self.new_face.get('oracle_text', '').split('\n'),
        ))
        diff = [x.rstrip() for x in diff if len(x.rstrip()) > 1 and not x.startswith('  ')]

        if diff:
            return [' rules:'] + diff
        else:
            return None

    def flavor_text(self):
        if self._simple_diff('flavor_text', ''):
            return f". flavor: <changed>"

    def pt(self):
        if self._simple_diff('power', '') or self._simple_diff('toughness', ''):
            power = self.new_face.get('power', '0')
            tough = self.new_face.get('toughness', '0')
            return f". p/t: {power}/{tough}"

    def loyalty(self):
        return self._simple_diff('loyalty', 'loyalty')

    def _ndiff(self, field):
        diff = list(difflib.ndiff(
            self.old_face.get(field, '').split('\n'),
            self.new_face.get(field, '').split('\n'),
        ))
        return [x.rstrip() for x in diff if len(x.rstrip()) > 1 and not x.startswith('  ') and not x.startswith('?')]

    def _simple_diff(self, field, display_name):
        if self.old_face.get(field) != self.new_face.get(field):
            return f". {display_name}: {self.new_face.get(field)}"
        else:
            return None
 

def empty_card_json():
    return {
        'object': 'card',
        'cmc': '0',
        'card_faces': [],
    }


def color_sort_key(color_ch):
    ch = color_ch.upper()
    if ch.isnumeric():
        return 0
    elif ch == 'W':
        return 1
    elif ch == 'U':
        return 2
    elif ch == 'B':
        return 3
    elif ch == 'R':
        return 4
    elif ch == 'G':
        return 5
    else:
        return 6


def color_symbol_to_name(symbol):
    if symbol == 'W':
        return 'white'
    elif symbol == 'U':
        return 'blue'
    elif symbol == 'B':
        return 'black'
    elif symbol == 'R':
        return 'red'
    elif symbol == 'G':
        return 'green'


def _divide_cards_by_type(cards):
    divided = {}
    for card in cards:
        for typ in CardConsts.CARD_TYPES:
            if typ in type_line(card).lower():
                divided.setdefault(typ, []).append(card)
                break
        else:
            divided.setdefault('other', []).append(card)

    for card_list in divided.values():
        card_list.sort(key=lambda x: (int(cmc(x)), x.name()))

    return divided


def group_cards_in_columns(cards):
    columns = []
    
    for color in 'WUBRG':
        colored = [x for x in cards if x.color_identity() == color]
        grouped = _divide_cards_by_type(colored)
        sections = []
        for card_type in CardConsts.CARD_TYPES + ('other',):
            sections.append(CardColumnSection(
                card_type,
                grouped.get(card_type, []),
            ))

        columns.append(CardColumn(color_symbol_to_name(color), sections))

    return columns
        
    groups['land'] = [x for x in cards if 'land' in type_line(x).lower()]
    groups['gold'] = [x for x in cards if len(x.color_identity()) > 1 and not 'land' in type_line(x).lower()]
    groups['gray'] = [x for x in cards if len(x.color_identity()) == 0 and not 'land' in type_line(x).lower()]


def cmc(card):
    return card.get_json().get('cmc', '0') or '0'


def type_line(card):
    return card.get_json().get('type_line', '')
