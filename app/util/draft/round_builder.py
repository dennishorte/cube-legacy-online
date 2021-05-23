import random

from app.models.cube_models import Cube
from app.util.cube_wrapper import CubeWrapper


class RoundBuilder(object):
    @staticmethod
    def build(setup: dict, user_data: list):
        # The set of all actions taken during this draft. Required fields are:
        # {
        #   'action': 'action_name',
        #   'user': user_id,
        #   'timestamp': timestamp,
        # }
        # Any number of other fields may be included for the specific draft.
        setup['built'] = True

        if setup['style'] == 'cube-pack':
            return RoundBuilder.cube_packs(setup, user_data)

        elif setup['style'] == 'rotisserie':
            return RoundBuilder.rotisserie(setup, user_data)

        else:
            raise ValueError(f"Unknown draft style: {setup['style']}")

    @staticmethod
    def cube_packs(setup: dict, user_data: dict):
        # Create a separate 'more_setup' dict here and merge it into the setup dict at the end.
        # Creating it here makes it easy to see what keys are added.
        more_setup = {
            'packs': [],  # pack id to pack mapping
        }

        cube = Cube.query.get(setup['cube_id'])
        wrapper = CubeWrapper(cube)
        card_data = wrapper.card_data()

        user_data_list = list(user_data.values())

        num_packs = setup['num_packs']
        pack_size = setup['pack_size']
        pack_count = len(user_data) * num_packs
        card_count = pack_count * pack_size

        if len(card_data) < card_count:
            raise ValueError(f"Not enough cards for {num_users} users * {num_packs} packs * {pack_size} cards")

        included_card_data = {}

        card_ids = list(card_data.keys())
        random.shuffle(card_ids)
        for i in range(pack_count):
            start = i * pack_size
            end = start + pack_size
            user_id = user_data_list[i // num_packs]['user_id']
            assert isinstance(user_id, str), "User ids should be strings"

            pack = {
                'pack_id': str(i),
                'card_ids': card_ids[start:end],
                'user_id': user_id,  # User who opens pack
                'round': i % num_packs,  # Order of pack opening
                'waiting_id': user_id,  # User who needs to pick from this pack
                'picked_ids': []
            }

            more_setup['packs'].append(pack)

            for card_id in pack['card_ids']:
                included_card_data[card_id] = card_data[card_id]

        setup.update(more_setup)

        return included_card_data


    @staticmethod
    def rotisserie(setup: dict, user_data: dict):
        cube = Cube.query.get(setup['cube_id'])
        wrapper = CubeWrapper(cube)
        card_data = wrapper.card_data()
        setup['card_ids'] = list(card_data.keys())
        setup['picked'] = {}

        return card_data
