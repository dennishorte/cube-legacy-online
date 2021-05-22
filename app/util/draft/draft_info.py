
class DraftInfo(object):
    def __init__(self, data):
        assert isinstance(data, dict), "Data must be of type dict"
        self.data = data

    ############################################################
    # Setup Functions

    def name_set(self, name):
        self.data['name'] = name

    def round_add(self, setup: dict):
        self.data.setdefault('rounds', []).append(setup)

    def user_add(self, user):
        self.data.setdefault('user_ids', []).append(user.id)

        user_data = {
            'user_id': user.id,
            'deck': {},
            'waiting_actions': [],
            'declined': False,
        }

        self.data.setdefault('user_data', []).append(user_data)

    ############################################################
    # Draft Functions

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

    def user_data(self, user_id: int = None):
        all_data = self.data.get('user_data', [])

        if user_id:
            for datum in all_data:
                if datum['user_id'] == user_id:
                    return datum

            raise ValueError(f"Unknown user with id {user_id}")
        else:
            return all_data

    def user_ids(self):
        return self.data.get('user_ids', [])

    def waiting(self, user):
        return True

    ############################################################
    # Debug Functions

    def dump(self):
        import json
        json.dumps(self.data, indent=2, sort_keys=True)
