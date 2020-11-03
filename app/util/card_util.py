import difflib
import re


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

    MULTICOLOR_MAP = {
        'BG': 'Golgari',
        'BR': 'Rakdos',
        'BU': 'Dimir',
        'BW': 'Orzhov',
        'GR': 'Gruul',
        'GU': 'Simic',
        'GW': 'Selesnya',
        'RU': 'Izzet',
        'RW': 'Boros',
        'UW': 'Azorius',

        'BGR': 'Jund',
        'BGU': 'Sultai',
        'BGW': 'Abzan',
        'BRU': 'Grixis',
        'BRW': 'Mardu',
        'BUW': 'Esper',
        'GRU': 'Temur',
        'GRW': 'Naya',
        'GUW': 'Bant',
        'RUW': 'Jeskai',

        'BGRU': 'Non-White',
        'BGRW': 'Non-Blue',
        'BGUW': 'Non-Red',
        'BRUW': 'Non-Green',
        'GRUW': 'Non-Black',

        'BGRUW': '5-Color',
    }
        

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


def cmc_from_string(cost_string):
    cost = 0
    
    cost_string = cost_string.upper()
    pattern = r"{(.*?)}"
    for mana_symbol in re.findall(pattern, cost_string):
        if mana_symbol.isnumeric():
            cost += int(mana_symbol)
            
        elif mana_symbol.startswith('2/'):
            cost += 2

        else:
            cost += 1

    return cost
