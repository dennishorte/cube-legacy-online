
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
            'user_data': [],  # [dict] (see user_add func for dict definition)
        }

        return DraftInfo(data)

    ############################################################
    # Setup Functions

    def card_data_add(self, data: dict):
        self.card_data().extend(data)

    def name_set(self, name):
        self.data['name'] = name

    def round_add(self, setup: dict):
        setup['built'] = False
        setup['started'] = False
        setup['finished'] = False
        self.rounds().append(setup)

    def user_add(self, user_model):
        if user_model.id in self.user_ids():
            return

        self.user_data().append({
            'id': user_model.id,
            'deck': {},
            'declined': False,
            'name': user_model.name,
        })

    ############################################################
    # General Draft Functions

    def can_be_drafted(self, card_id, user):
        return True

    def can_be_seen(self, card_id, user):
        return True

    def card(self, card_id):
        card_id = str(card_id)
        return self.data['card_data'][card_id]

    def card_data(self):
        return self.data['card_data']

    def current_round(self, user_id):
        user_id = self._format_user_id(user_id)
        if self.rounds():
            return self.rounds()[0]
        else:
            return None

    def is_complete(self):
        return all([x['finished'] for x in self.rounds()])

    def json_string(self):
        return json.dumps(self.data)

    def num_picked(self):
        pass

    def pick_do(self, user_id, card_id):
        user_id = self._format_user_id(user_id)
        pass

    def pick_undo(self, user_id):
        user_id = self._format_user_id(user_id)
        pass

    def round_finalize(self, rnd):
        assert self.round_is_complete(rnd), "Can't finalize an unfinished round."
        rnd['finished'] = True
        index = self.rounds().indexof(rnd)
        assert index > -1, "Unable to get proper index for round."

        if index + 1 < len(self.rounds()):
            self.round_start(self.rounds()[index + 1])

    def round_is_complete(self, rnd):
        if rnd['style'] == 'cube-pack':
            return len(rnd['picked_ids']) == setup['num_packs'] * setup['pack_size'] * len(self.user_data())

        elif rnd['style'] == 'rotisserie':
            return len(rnd['picked_ids']) == setup['num_cards'] * len(self.user_data())

        else:
            raise ValueError(f"Unknown round style: {rnd['style']}")

    def round_start(self, rnd):
        rnd['started'] = True

        if rnd['style'] == 'cube-pack':
            for pack in rnd['packs']:
                if pack['pack_num'] == 0:
                    pack['opened'] = True

        elif rnd['style'] == 'rotisserie':
            pass

        else:
            raise ValueError(f"Unknown round style: {rnd['style']}")

    def rounds(self):
        return self.data.get('rounds', [])

    def user_decline(self, user_id, value=True):
        user_id = self._format_user_id(user_id)
        datum = self.user_data(user_id)
        datum['declined'] = value

    def user_data(self, user_id = None):
        user_id = self._format_user_id(user_id)
        all_data = self.data['user_data']

        if user_id:
            for datum in all_data:
                if datum['id'] == user_id:
                    return datum

            raise ValueError(f"Unable to find data for user_id: {user_id}")
        else:
            return all_data

    def user_ids(self):
        return [x['id'] for x in self.user_data()]

    def waiting(self, user_id):
        current_round = self.current_round(user_id)
        if not current_round or 'built' not in current_round:
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

    def is_scar_round(self, user_id):
        return False

    def next_pack(self, user_id):
        user_id = self._format_user_id(user_id)
        current_round = self.current_round(user_id)

        if not current_round['style'].endswith('-pack'):
            raise RuntimeError(f"User {user_id}'s current round is not a pack round")

        if not current_round.get('built'):
            return None

        waiting_packs = list(filter(lambda x: x['waiting_id'] == user_id, current_round['packs']))
        waiting_packs.sort(key=lambda pack: (pack['pack_num'], -len(pack['picked_ids'])))

        if waiting_packs and waiting_packs[0]['opened']:
            return waiting_packs[0]
        else:
            return None

    def scar_options(self, user_id):
        return []


    ############################################################
    # Debug Functions

    def dump(self):
        import json
        json.dumps(self.data, indent=2, sort_keys=True)


    ############################################################
    # Internal Functions

    def _format_user_id(self, user_id):
        if isinstance(user_id, str):
            return int(user_id)
        elif isinstance(user_id, dict):
            return self._format_user_id(user_id['id'])
        elif hasattr(user_id, 'id'):
            return self._format_user_id(user_id = user_id.id)
        else:
            return user_id
