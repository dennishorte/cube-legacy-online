import re

from app.util import card_util
from app.util.card_util import cmc_from_string
from app.util.card_util import color_sort_key
from app.util.enum import Layout


class CardJsonWrapper(object):
    def __init__(self, card_json):
        self.data = card_json

    def back(self):
        if len(self.card_faces()) > 1:
            return self.card_faces()[1]
        else:
            return None

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

    def front(self):
        return self.card_faces()[0]

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

    def is_creature(self):
        return 'creature' in self.front().get('type_line', '').lower()

    def is_land(self):
        return 'land' in self.front().get('type_line', '').lower()

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
