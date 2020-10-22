import difflib
from collections import UserDict
from collections import UserList

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


class CardDiffer(object):
    def __init__(self, old, new):
        self.old = old
        self.new = new

        self.old_faces = self.old.card_faces()
        self.new_faces = self.new.card_faces()

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
            self.old_faces[0].get('oracle_text', '').split('\n'),
            self.new_faces[0].get('oracle_text', '').split('\n'),
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
            power = self.new_faces[0].get('power', '0')
            tough = self.new_faces[0].get('toughness', '0')
            return f". p/t: {power}/{tough}"

    def loyalty(self):
        return self._simple_diff('loyalty', 'loyalty')

    def _ndiff(self, field):
        diff = list(difflib.ndiff(
            self.old_faces[0].get(field, '').split('\n'),
            self.new_faces[0].get(field, '').split('\n'),
        ))
        return [x.rstrip() for x in diff if len(x.rstrip()) > 1 and not x.startswith('  ') and not x.startswith('?')]

    def _simple_diff(self, field, display_name):
        if self.old_faces[0].get(field) != self.new_faces[0].get(field):
            return f". {display_name}: {self.new_faces[0].get(field)}"
        else:
            return None
 

def empty_card_json():
    return {
        'object': 'card',
        'cmc': '0',
        'card_faces': [],
    }
