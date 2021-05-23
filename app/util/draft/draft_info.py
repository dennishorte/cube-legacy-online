
class DraftInfo(object):
    def __init__(self, data):
        assert isinstance(data, dict), "Data must be of type dict"
        self.data = data

    @staticmethod
    def factory():
        data = {
            'card_data': {},  # cube_card.id: card_json
            'name': '',
            'rounds': [],  # dicts of round setup info
            'user_data': {},  # User.id: dict (see user_add func)
        }

        return DraftInfo(data)

    ############################################################
    # Setup Functions

    def card_data_add(self, data: dict):
        self.card_data().extend(data)

    def name_set(self, name):
        self.data['name'] = name

    def round_add(self, setup: dict):
        self.rounds().append(setup)

    def user_add(self, user):
        user_id = str(user.id)  # Due to json serialization, always use strings for user ids.

        if user_id in self.user_data():
            return

        self.user_data()[user_id] = {
            'user_id': user_id,
            'deck': {},
            'declined': False,
            'name': user.name,
        }

    ############################################################
    # General Draft Functions

    def can_be_drafted(self, card_id, user):
        return True

    def can_be_seen(self, card_id, user):
        return True

    def card(self, card_id):
        return self.data['card_data'][card_id]

    def card_data(self):
        return self.data['card_data']

    def current_round(self, user_id):
        if self.rounds():
            return self.rounds()[0]
        else:
            return None

    def is_complete(self):
        pass

    def json_string(self):
        return json.dumps(self.data)

    def num_picked(self):
        pass

    def pick_do(self, user, card_id):
        pass

    def pick_undo(self, user):
        pass

    def rounds(self):
        return self.data.get('rounds', [])

    def user_decline(self, user, value=True):
        datum = self.user_data(user.id)
        datum['declined'] = value

    def user_data(self, user_id = None):
        all_data = self.data['user_data']

        if user_id:
            user_id = str(user_id)
            return all_data[user_id]
        else:
            return all_data

    def user_ids(self):
        return list(self.user_data().keys())

    def waiting(self, user_id):
        current_round = self.current_round('user_id')
        if not current_round:
            return False

        round_style = current_round['style']

        if round_style == 'cube-pack':
            return self.next_pack(user_id) is not None
        elif round_style == 'rotisserie':
            return True
        else:
            raise ValueError(f"Unknown round type: {round_style}")


    ############################################################
    # Pack Draft Functions

    def next_pack(self, user_id):
        if hasattr(user_id, 'id'):
            user_id = str(user_id.id)

        current_round = self.current_round(user_id)

        if not current_round['style'].endswith('-pack'):
            raise RuntimeError(f"User {user_id}'s current round is not a pack round")

        if not current_round.get('built'):
            return None

        waiting_packs = list(filter(lambda x: x['waiting_id'] == user_id, current_round['packs']))
        waiting_packs.sort(key=lambda pack: (pack['round'], -len(pack['picked_ids'])))


    ############################################################
    # Debug Functions

    def dump(self):
        import json
        json.dumps(self.data, indent=2, sort_keys=True)
