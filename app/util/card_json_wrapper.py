from app.util import card_util
from app.util.enum import Layout


class CardJsonWrapper(object):
    def __init__(self, data):
        self.data = data

    def back(self):
        if len(self.data['card_faces']) > 1:
            return self.data['card_faces'][1]
        else:
            return None

    def color_identity(self):
        pattern = r"{(.*?)}"
        identity = set()
        for face in self.data['card_faces']:
            texts = [face['mana_cost']] + re.findall(pattern, face['oracle_text'])
            for text in texts:
                for ch in face['mana_cost'].upper():
                    if ch in 'WUBRG':
                        identity.add(ch)

        identity = sorted(identity, key=color_sort_key)
        identity = ''.join(identity)

        return identity

    def cmc(self):
        cost = 0
        cost += card_util.cmc_from_string(self.front()['mana_cost'])

        if self.layout() == Layout.split.name:
            cost += card_util.cmc_from_string(self.back()['mana_cost'])

        return cost

    def front(self):
        return self.data['card_faces'][0]

    def has_type(self, card_type):
        return card_type.lower() in self.front().get('type_line', '').lower()

    def is_creature(self):
        return 'creature' in self.front().get('type_line', '').lower()

    def is_land(self):
        return 'land' in self.front().get('type_line', '').lower()

    def layout(self):
        return self.data['layout']

    def name(self):
        return self.data['name']

    def oracle_text(self):
        return self.data['oracle_text']

    def rarity(self):
        return self.data['rarity']

    def type_line(self):
        return self.data.get('type_line', 'NO_TYPE')
