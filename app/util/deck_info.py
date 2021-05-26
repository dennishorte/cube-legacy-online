

class DeckInfo(object):
    def __init__(self, data):
        self.data = data

    @staticmethod
    def factory():
        data = {
            'creature': {},
            'non_creature': {},
            'basic_land': {},
            'command': [],
        }
        return DeckInfo(data)

    def card_ids(self):
        id_list = []
        for x in ('creature', 'non_creature', 'basic_land'):
            for _, card_list in self.data[x].items():
                id_list += card_list

        id_list += self.data['command']

        return id_list

    def command(self):
        return self.data['command']
