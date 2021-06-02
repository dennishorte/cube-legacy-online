from app.util.card_json_wrapper import CardJsonWrapper


class DeckInfo(object):
    def __init__(self, data: dict, card_data: dict):
        self.data = data
        self.card_data = card_data  # Formatted as {card_id: CubeCard.get_json()}

    @staticmethod
    def factory(name: str, card_data: dict):
        data = {
            'name': name or 'unnamed deck',
            'maindeck': {
                'creature': {},
                'non_creature': {},
            },
            'sideboard': {
                'creature': {},
                'non_creature': {},
            },
            'basic_land': {
                'forest': 0,
                'island': 0,
                'mountain': 0,
                'plains': 0,
                'swamp': 0,
                'wastes': 0,
                'snow-covered': False,
            },
            'command': [],
        }

        for i in range(7):
            data['maindeck']['creature'][str(i)] = []
            data['sideboard']['creature'][str(i)] = []
            data['maindeck']['non_creature'][str(i)] = []
            data['sideboard']['non_creature'][str(i)] = []

        data['maindeck']['creature']['7+'] = []
        data['sideboard']['creature']['7+'] = []
        data['maindeck']['non_creature']['7+'] = []
        data['sideboard']['non_creature']['7+'] = []

        return DeckInfo(data, card_data)

    def add_card(self, card_id):
        card = self.card_wrapper(card_id)

        if card.has_type('conspiracy'):
            self.command.append(card_id)

        elif card.is_creature():
            print('added to creatures')
            self.data['maindeck']['creature'][str(card.cmc())].append(card_id)

        else:
            print('added to non creatures')
            self.data['maindeck']['non_creature'][str(card.cmc())].append(card_id)

    def basic_counts(self, name: str):
        name = name.lower()
        return self.data['basic_land'][name]

    def card_ids(self):
        id_list = []
        for x in ('creature', 'non_creature'):
            for _, card_list in self.data[x].items():
                id_list += card_list

        id_list += self.data['command']

        return id_list

    def card_wrapper(self, card_id):
        return CardJsonWrapper(self.card_data[str(card_id)])

    def command_ids(self):
        return self.data['command']

    def name(self):
        return self.data['name']