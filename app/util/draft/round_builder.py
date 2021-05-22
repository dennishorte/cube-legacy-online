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
        setup['actions'] = {}

        if setup['style'] == 'cube_pack':
            return RoundBuilder.cube_packs(setup, user_data)

        elif setup['style'] == 'rotisserie':
            return RoundBuilder.rotisserie(setup, user_data)

    @staticmethod
    def cube_packs(setup: dict, user_data: list):
        cube = Cube.query.get(setup['cube_id'])
        wrapper = CubeWrapper(cube)
        card_data = wrapper.card_data()

        pack_count = len(user_data) * setup['num_packs']
        card_count = pack_count * setup['pack_size']

        if len(card_data) < card_count:
            raise ValueError(f"Not enough cards for {num_users} users * {setup['num_packs']} packs * {setup['pack_size']} cards")

        setup['packs'] = []

        random.shuffle(card_data)
        for i in range(pack_count):
            start = i * setup['pack_size']
            end = start + setup['pack_size']
            setup['packs'].append(card_data[start:end])


    @staticmethod
    def rotisserie(setup: dict, user_data: list):
        cube = Cube.query.get(setup['cube_id'])
        wrapper = CubeWrapper(cube)
        setup['cards'] = wrapper.card_data()
        setup['picked'] = {}
