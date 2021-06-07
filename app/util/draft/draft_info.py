from app.util.deck_info import DeckInfo


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
        self.card_data().update(data)

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
            'deck_data': DeckInfo.factory(
                f"{user_model.name}'s {self.name()} deck",
                self.card_data()
            ).data,
            'declined': False,
            'name': user_model.name,
        })


    ############################################################
    # Deck Functions

    def deck_info(self, user_id):
        user_data = self.user_data(user_id)
        return DeckInfo(user_data['deck_data'], self.card_data())

    def deck_update(self, user_id, deck_json):
        user_data = self.user_data(user_id)
        user_data['deck_data'] = deck_json

        # If there are any cards in the user's deck that aren't in the draft cards,
        # add them into the draft cards.
        deck_info = self.deck_info(user_id)
        for card_id in deck_info.card_ids():
            if card_id not in self.card_data():
                from app.models.cube_models import CubeCard
                card = CubeCard.query.get(card_id)
                self.card_data_add({
                    str(card_id): card.get_json(),
                })


    ############################################################
    # General Draft Functions

    def can_be_drafted(self, user_id, card_id):
        user_id = self._format_user_id(user_id)
        current_round = self.current_round(user_id)

        if current_round['style'] == 'cube-pack':
            pack = self.next_pack(user_id)
            if not pack:
                return False
            else:
                return card_id not in pack['picked_ids']

        else:
            return True

    def can_be_seen(self, user_id, card_id):
        user_id = self._format_user_id(user_id)
        current_round = self.current_round(user_id)

        if current_round['style'] == 'cube-pack':
            # In a pack draft, the user can see any cards that were in the pack when they
            # first saw it.
            pack = self.next_pack(user_id)
            for event in pack['events']:
                if event['user_id'] == user_id:
                    return True
                elif event['name'] == 'card_picked' and event['card_id'] == card_id:
                    return False

            return True

        else:
            return True

    def card(self, card_id):
        card_id = str(card_id)
        return self.data['card_data'][card_id]

    def card_data(self):
        return self.data['card_data']

    def current_round(self, user_id):
        user_id = self._format_user_id(user_id)
        for rnd in self.rounds():
            if not rnd['finished']:
                return rnd

        return None

    def is_complete(self):
        return all([x['finished'] for x in self.rounds()])

    def json_string(self):
        return json.dumps(self.data)

    def name(self):
        return self.data['name']

    def pick_do(self, user_id, card_id):
        user_id = self._format_user_id(user_id)
        pass

    def pick_undo(self, user_id):
        user_id = self._format_user_id(user_id)
        pass

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

    def seat_index(self, user_id):
        user_id = self._format_user_id(user_id)
        for i, datum in enumerate(self.user_data()):
            if datum['id'] == user_id:
                return i

        raise ValueError(f"Unknown user id {user_id}")

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

    def make_pack_pick(self, user_id, card_id):
        user_id = self._format_user_id(user_id)
        card_id = int(card_id)
        pack = self.next_pack(user_id)
        current_round = self.current_round(user_id)

        # ensure the card is in the pack
        if card_id not in pack['card_ids']:
            raise ValueError(f"Card {card_id} is not in pack {pack['pack_id']}")

        # ensure the card has not already been picked
        if card_id in pack['picked_ids']:
            raise ValueError(f"Card {card_id} is picked from pack {pack['pack_id']}")

        # ensure this user is allowed to pick this card
        if not self.can_be_drafted(user_id, card_id):
            raise ValueError(f"User {user_id} is not allowed to draft card {card_id}")

        # Make the pick
        pack['picked_ids'].append(card_id)
        pack['events'].append({
            'name': 'card_picked',
            'user_id': user_id,
            'card_id': card_id,
        })
        self.deck_info(user_id).add_card(card_id)

        # Pass the pack or open the next pack
        if len(pack['picked_ids']) == len(pack['card_ids']):
            self._pack_open_next(user_id, current_round, pack)
        else:
            self._pack_pass(current_round, pack)

        self._check_for_pack_round_complete(current_round)

    def next_pack(self, user_id):
        user_id = self._format_user_id(user_id)
        current_round = self.current_round(user_id)

        if not current_round['style'].endswith('-pack'):
            raise RuntimeError(f"User {user_id}'s current round is not a pack round")

        if not current_round.get('built'):
            return None

        waiting_packs = list(filter(lambda x: x['waiting_id'] == user_id, current_round['packs']))
        waiting_packs.sort(key=lambda pack: (pack['pack_num'], len(pack['picked_ids'])))

        if waiting_packs and waiting_packs[0]['opened']:
            return waiting_packs[0]
        else:
            return None

    def num_packs_waiting_for_pack_num(self, user_id, pack_num):
        round_info = self.current_round(user_id)
        assert round_info['style'] == 'cube-pack', f"Incorrect round type for num_picks_for_pack: {round_info['style']}"

        waiting_count = 0
        for pack in round_info['packs']:
            if pack['pack_num'] == pack_num and pack['waiting_id'] == user_id:
                waiting_count += 1

        return waiting_count

    def num_picks_for_pack_num(self, user_id, pack_num):
        round_info = self.current_round(user_id)
        assert round_info['style'] == 'cube-pack', f"Incorrect round type for num_picks_for_pack: {round_info['style']}"

        pick_count = 0
        for pack in round_info['packs']:
            if pack['pack_num'] == pack_num:
                for event in pack['events']:
                    if event['user_id'] == user_id and event['name'] == 'card_picked':
                        pick_count += 1

        return pick_count

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
            return self._format_user_id(user_id.id)
        else:
            return user_id

    def _check_for_pack_round_complete(self, rnd):
        for pack in rnd['packs']:
            if pack['waiting_id'] != 'pack_complete':
                return

        self._round_advance(rnd)

    def _pack_open_next(self, user_id, current_round, current_pack):
        current_pack['waiting_id'] = 'pack_complete'
        next_pack_num = current_pack['pack_num'] + 1

        # No more packs for this user
        if next_pack_num >= current_round['num_packs']:
            return

        for p in current_round['packs']:
            if p['user_id'] == user_id and p['pack_num'] == next_pack_num:
                p['opened'] = True
                return

    def _pack_pass(self, rnd, pack):
        # Decide direction to pass
        if pack['pack_num'] % 2 == 0:
            increment = 1
        else:
            increment = -1

        seat_index = self.seat_index(pack['waiting_id'])
        next_index = (seat_index + increment) % len(self.user_data())

        pack['waiting_id'] = self.user_data()[next_index]['id']

    def _round_advance(self, current_round):
        current_round['finished'] = True
