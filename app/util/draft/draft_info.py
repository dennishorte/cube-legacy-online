import random

from app.util.card_json_wrapper import CardJsonWrapper
from app.util.deck_info import DeckInfo
from app.util.game_results import GameResults


class DraftInfo(object):
    def __init__(self, data):
        assert isinstance(data, dict), "Data must be of type dict"
        self.data = data

        self._results = {}

    @staticmethod
    def factory(draft_id: int):
        data = {
            'card_data': {},  # cube_card.id: card_json
            'draft_id': draft_id,
            'messages': [],
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

            # draft matters info
            'cogwork_librarian_ids': [],
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
            card_id = self._format_card_id(card_id)
            if card_id not in self.card_data():
                from app.models.cube_models import CubeCard
                card = CubeCard.query.get(card_id)
                self.card_data_add({
                    str(card_id): card.get_json(),
                })


    ############################################################
    # Draft Matters Functions

    def cogwork_librarian_has(self, user_id):
        user_id = self._format_user_id(user_id)
        user_data = self.user_data(user_id)

        # For backwards compatibility
        if 'cogwork_librarian_ids' not in user_data:
            user_data['cogwork_librarian_ids'] = []

            deck = self.deck_info(user_id)
            for card_id in deck.card_ids():
                card = deck.card_wrapper(card_id)
                if 'cogwork librarian' in card.name().lower():
                    user_data['cogwork_librarian_ids'].append(card_id)

        return len(user_data['cogwork_librarian_ids']) > 0

    def cogwork_librarian_maybe_add(self, user_id, card_id):
        user_id = self._format_user_id(user_id)
        user_data = self.user_data(user_id)

        card_id = self._format_card_id(card_id)
        card = self.card_wrapper(card_id)

        # For backwards compatibility
        if 'cogwork_librarian_ids' not in user_data:
            user_data['cogwork_librarian_ids'] = []

        if 'cogwork librarian' in card.name().lower():
            user_data['cogwork_librarian_ids'].append(card_id)

            from app.models.user_models import User
            user = User.query.get(user_id)

            # For backwards compatibility
            if not self.data['messages']:
                self.data['messages'] = []

            self.data['messages'].append(f"{user.name} drafted {card.name()}")

    def cogwork_librarian_use(self, user_id):
        user_id = self._format_user_id(user_id)

        if self.current_round(user_id)['style'] not in ('cube-pack', 'set-pack'):
            raise RuntimeError(f"Can't use cogwork librarian in this round type")

        # Remove from user's card pool
        user_data = self.user_data(user_id)
        card_id = user_data['cogwork_librarian_ids'].pop()
        self.deck_info(user_id).card_remove_by_id(card_id)

        # For backwards compatibility
        if not self.data['messages']:
            self.data['messages'] = []

        # Public notification of using a face up card
        card = self.card_wrapper(card_id)
        self.data['messages'].append(f"{user_data['name']} put {card.name()} back in a pack")

        # Mark that this user gets an additional pick from this pack
        pack = self.next_pack(user_id)

        # For backwards compatibility
        if 'waiting_picks' not in pack:
            pack['waiting_picks'] = 1

        pack['waiting_picks'] += 1


    ############################################################
    # General Draft Functions

    def can_be_drafted(self, user_id, card_id):
        card_id = self._format_card_id(card_id)
        user_id = self._format_user_id(user_id)
        current_round = self.current_round(user_id)

        if current_round['style'] in ('cube-pack', 'set-pack'):
            pack = self.next_pack(user_id)
            if not pack:
                return False
            elif self._user_just_scarred_card(user_id, card_id):
                return False
            elif self.is_scar_round(user_id) and not self.user_scarring_complete(user_id):
                return False
            else:
                return card_id not in pack['picked_ids']

        elif current_round['style'] == 'rotisserie':
            return card_id not in current_round['picked_ids']

        else:
            return True

    def can_be_seen(self, user_id, card_id):
        card_id = self._format_card_id(card_id)
        user_id = self._format_user_id(user_id)
        current_round = self.current_round(user_id)

        if current_round['style'] in ('cube-pack', 'set-pack'):
            # In a pack draft, the user can see any cards that were in the pack when they
            # first saw it.
            pack = self.next_pack(user_id)
            for event in pack['events']:
                if event['user_id'] == user_id:
                    return True
                elif event['name'] == 'card_picked' and event['card_id'] == card_id:
                    return False

            return True

        elif current_round['style'] == 'rotisserie':
            return True

        else:
            return True

    def card(self, card_id):
        card_id = self._format_card_id(card_id)
        return self.data['card_data'][card_id]

    def card_data(self):
        return self.data['card_data']

    def card_wrapper(self, card_id):
        return CardJsonWrapper(self.card(card_id))

    def cards_picked(self, user_id):
        user_id = self._format_user_id(user_id)

        card_ids = []

        for rnd in self.rounds():
            if not rnd['built']:
                continue

            if rnd['style'] == 'rotisserie':
                for event in rnd['events']:
                    if event['user_id'] == user_id and event['name'] == 'card_picked':
                        card_ids.append(event['card_id'])

        return card_ids

    def current_round(self, user_id=None):
        for rnd in self.rounds():
            if not rnd['finished']:
                return rnd

        return None

    def draft_id(self):
        return self.data['draft_id']

    def is_complete(self):
        return all([x['finished'] for x in self.rounds()])

    def is_scar_round(self, user_id):
        current_round = self.current_round(user_id)

        if current_round['style'] == 'cube-pack':
            pack = self.next_pack(user_id)
            return (
                pack
                and len(pack['picked_ids']) == 0
                and pack['pack_num'] in current_round['scar_rounds']
            )

        else:
            return False

    def json_string(self):
        return json.dumps(self.data)

    def messages(self):
        return self.data.get('messages', [])

    def name(self):
        return self.data['name']

    def results(self, user1, user2):
        if not self._results:
            self._results = self._all_match_results()

        return self._results.get(user1, {}).get(user2, GameResults())

    def round_start(self, rnd):
        rnd['started'] = True

        if rnd['style'] in ('cube-pack', 'set-pack'):
            for pack in rnd['packs']:
                if pack['pack_num'] == 0:
                    pack['opened'] = True

        elif rnd['style'] == 'rotisserie':
            # Adjust the player order to match the rotisserie first player.
            first_id = rnd['waiting_id']
            user_data = self.user_data()
            assert any([x['id'] == first_id for x in user_data]), "Invalid user id as first player id"

            while user_data[0]['id'] != first_id:
                user_data.append(user_data.pop(0))

        else:
            raise ValueError(f"Unknown round style: {rnd['style']}")

    def rounds(self):
        return self.data.get('rounds', [])

    def scars(self, user_id):
        from app.models.cube_models import Scar

        user_id = self._format_user_id(user_id)

        if not self.is_scar_round(user_id):
            return None

        if self.user_scarring_complete(user_id):
            return None

        scars = Scar.draft_v2_get(self.draft_id(), user_id)

        if not scars:
            scars = Scar.draft_v2_lock(
                draft_id = self.draft_id(),
                cube_id = self.current_round(user_id)['cube_id'],
                user_id = user_id,
                count = 2,
            )

        assert len(scars) == 2, "Incorrect number of locked scars. Something is wrong."

        return scars

    def scars_change(self, user_id):
        from app.models.cube_models import Scar
        user_id = self._format_user_id(user_id)
        Scar.draft_v2_unlock(self.draft_id(), user_id)

    def seat_index(self, user_id):
        user_id = self._format_user_id(user_id)
        for i, datum in enumerate(self.user_data()):
            if datum['id'] == user_id:
                return i

        raise ValueError(f"Unknown user id {user_id}")

    def start(self):
        # Randomize seating
        random.shuffle(self.user_data())

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
        user_id = self._format_user_id(user_id)
        current_round = self.current_round(user_id)
        if not current_round or 'built' not in current_round:
            return False

        round_style = current_round['style']

        if round_style in ('cube-pack', 'set-pack'):
            return self.next_pack(user_id) is not None
        elif round_style == 'rotisserie':
            return current_round.get('waiting_id') == user_id
        else:
            raise ValueError(f"Unknown round type: {round_style}")


    ############################################################
    # Pack Draft Functions

    def make_pack_pick(self, user_id, card_id):
        card_id = self._format_card_id(card_id)
        user_id = self._format_user_id(user_id)
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

        # Draft matters checks
        self.cogwork_librarian_maybe_add(user_id, card_id)

        # Open the next pack
        if len(pack['picked_ids']) == len(pack['card_ids']):
            self._pack_open_next(user_id, current_round, pack)

        # Maybe this player needs to take another card?
        elif 'waiting_picks' in pack and pack['waiting_picks'] > 1:
            pack['waiting_picks'] -= 1

        # Otherwise, pass the pack to the next player
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
        assert round_info['style'] in ('cube-pack', 'set-pack'), f"Incorrect round type for num_picks_for_pack: {round_info['style']}"

        waiting_count = 0
        for pack in round_info['packs']:
            if pack['pack_num'] == pack_num and pack['waiting_id'] == user_id:
                waiting_count += 1

        return waiting_count

    def num_picks_for_pack_num(self, user_id, pack_num):
        round_info = self.current_round(user_id)
        assert round_info['style'] in ('cube-pack', 'set-pack'), f"Incorrect round type for num_picks_for_pack: {round_info['style']}"

        pick_count = 0
        for pack in round_info['packs']:
            if pack['pack_num'] == pack_num:
                for event in pack['events']:
                    if event['user_id'] == user_id and event['name'] == 'card_picked':
                        pick_count += 1

        return pick_count

    def user_did_scar(self, user_id, card_id):
        card_id = self._format_card_id(card_id)
        user_id = self._format_user_id(user_id)
        pack = self.next_pack(user_id)
        pack['events'].append({
            'name': 'scar_applied',
            'pack_num': self.next_pack(user_id)['pack_num'],
            'user_id': user_id,
            'card_id': card_id,
        })

    def user_scarring_complete(self, user_id):
        user_id = self._format_user_id(user_id)
        pack = self.next_pack(user_id)

        for event in pack['events']:
            if event['name'] == 'scar_applied' and event['user_id'] == user_id and event['pack_num'] == pack['pack_num']:
                return True

        return False

    ############################################################
    # Rotisserie Functions

    def card_table(self, user_id):
        user_id = self._format_user_id(user_id)
        current_round = self.current_round(user_id)
        card_ids = set(current_round['card_ids'])

        card_data = {
            cid: cjson
            for cid, cjson in self.card_data().items()
            if cid in card_ids
        }

        from app.util.card_table_json import CardTableJson
        return CardTableJson(card_data)

    def make_rotisserie_pick(self, user_id, card_id):
        card_id = self._format_card_id(card_id)
        user_id = self._format_user_id(user_id)
        current_round = self.current_round(user_id)

        # ensure it is the current user's turn to pick
        if current_round['waiting_id'] != user_id:
            raise ValueError(f"It is not {user_id}'s turn to pick")

        # ensure the card is in the current_round
        if card_id not in current_round['card_ids']:
            raise ValueError(f"Card {card_id} is not in rotisserie")

        # ensure the card has not already been picked
        if card_id in current_round['picked_ids']:
            raise ValueError(f"Card {card_id} is picked from rotisserie")

        # ensure this user is allowed to pick this card
        if not self.can_be_drafted(user_id, card_id):
            raise ValueError(f"User {user_id} is not allowed to draft card {card_id}")

        # Calculate direction for next step before making pick
        direction = self.rotisserie_next_direction()

        # Make the pick
        current_round['picked_ids'].append(card_id)
        current_round['events'].append({
            'name': 'card_picked',
            'user_id': user_id,
            'card_id': card_id,
        })
        self.deck_info(user_id).add_card(card_id)

        # Draft matters checks
        self.cogwork_librarian_maybe_add(user_id, card_id)

        # Get the direction for the next player
        user_ids = self.user_ids()
        user_index = user_ids.index(user_id)
        next_index = user_index + direction
        current_round['waiting_id'] = user_ids[next_index]

        # Check if the round is finished
        if len(current_round['picked_ids']) == len(self.user_ids()) * current_round['num_cards']:
            self._round_advance(current_round)

    def rotisserie_next_direction(self):
        row, col = self.rotisserie_waiting_position()

        if col == 0:
            if row + 1 == len(self.user_ids()):
                return 0
            else:
                return 1

        else:
            if row == 0:
                return 0
            else:
                return -1

    def rotisserie_waiting_position(self):
        current_round = self.current_round()

        if current_round['style'] != 'rotisserie':
            raise RuntimeError("It is not currently a rotisserie round")

        num_users = len(self.user_ids())
        num_picked = len(current_round['picked_ids'])
        round_length = num_users * 2
        round_position = num_picked % round_length

        if round_position < num_users:
            row = round_position
        else:
            row = round_length - round_position - 1

        col = round_position // num_users

        return row, col


    ############################################################
    # Debug Functions

    def dump(self):
        import json
        json.dumps(self.data, indent=2, sort_keys=True)


    ############################################################
    # Internal Functions

    def _format_card_id(self, card_id):
        if isinstance(card_id, int):
            return str(card_id)
        elif isinstance(card_id, dict):
            return self._format_card_id(card_id['cube_card_id'])
        elif hasattr(card_id, 'id'):
            return self._format_card_id(card_id.id())
        else:
            return card_id

    def _format_user_id(self, user_id):
        if isinstance(user_id, str):
            return int(user_id)
        elif isinstance(user_id, dict):
            return self._format_user_id(user_id['id'])
        elif hasattr(user_id, 'id'):
            return self._format_user_id(user_id.id)
        else:
            return user_id

    def _all_match_results(self):
        from app.models.game_models import Game
        from app.models.game_models import GameDraftV2Link

        game_links = GameDraftV2Link.query.filter(GameDraftV2Link.draft_id == self.draft_id()).all()
        all_game_ids = [x.game_id for x in game_links]
        all_games = Game.query.filter(Game.id.in_(all_game_ids)).all()

        results_map = {}

        for game in all_games:
            all_users = [x.user_id for x in game.user_links]
            for user_id in all_users:
                user_results = results_map.setdefault(user_id, {})
                for opp_id in all_users:
                    if user_id == opp_id:
                        continue

                    match_results = user_results.setdefault(opp_id, GameResults())
                    match_results.add_result(game.state.result_for(user_id))

        return results_map


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

    def _user_just_scarred_card(self, user_id, card_id):
        user_id = self._format_user_id(user_id)
        pack = self.next_pack(user_id)

        if len(pack['picked_ids']) > 0:
            return False

        for event in pack['events']:
            if (
                    event['name'] == 'scar_applied'
                    and event['user_id'] == user_id
                    and event['card_id'] == card_id
            ):
                return True

        return False
