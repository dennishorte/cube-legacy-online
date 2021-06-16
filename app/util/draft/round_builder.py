import random

from app.models.cube_models import Cube
from app.models.cube_models import CubeCard
from app.util.cube_wrapper import CubeWrapper


class RoundBuilder(object):
    @staticmethod
    def build(setup: dict, user_data: list):
        setup['built'] = True

        if setup['style'] == 'cube-pack':
            return RoundBuilder.cube_packs(setup, user_data)

        elif setup['style'] == 'set-pack':
            return RoundBuilder.set_packs(setup, user_data)

        elif setup['style'] == 'rotisserie':
            return RoundBuilder.rotisserie(setup, user_data)

        else:
            raise ValueError(f"Unknown draft style: {setup['style']}")

    @staticmethod
    def cube_packs(setup: dict, user_data: list):
        # Create a separate 'more_setup' dict here and merge it into the setup dict at the end.
        # Creating it here makes it easy to see what keys are added.
        more_setup = {
            'packs': [],  # pack id to pack mapping
            'picks': [],  # { 'user_id': id, 'pack_id': pack_id, 'card_id': card_id }
        }

        cube = Cube.query.get(setup['cube_id'])
        wrapper = CubeWrapper(cube)
        card_data = wrapper.card_data(include_removed=False)

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
            user_id = user_data[i // num_packs]['id']

            pack = {
                'pack_id': i,
                'card_ids': card_ids[start:end],
                'user_id': user_id,  # User who opens pack
                'pack_num': i % num_packs,  # Order of pack opening
                'waiting_id': user_id,  # User who needs to pick from this pack
                'picked_ids': [],
                'events': [],
                'opened': False,
            }

            more_setup['packs'].append(pack)

            for card_id in pack['card_ids']:
                included_card_data[card_id] = card_data[card_id]

        setup.update(more_setup)

        return included_card_data


    @staticmethod
    def set_packs(setup: dict, user_data: list):
        more_setup = {
            'packs': [],  # dict, defined below
            'picks': [],  # { 'user_id': id, 'pack_id': pack_id, 'card_id': card_id }
            'num_packs': 3,
            'pack_size': 15,
        }

        pack_card_ids, included_card_data = RoundBuilder._make_set_packs(
            cube_id = setup['cube_id'],
            count = len(user_data) * 3,
        )

        for user_num in range(len(user_data)):
            for pack_num in range(3):
                pack_index = user_num * 3 + pack_num
                more_setup['packs'].append({
                    'pack_id': pack_index,
                    'card_ids': pack_card_ids[pack_index],
                    'user_id': user_data[user_num]['id'],  # User who opens pack
                    'waiting_id': user_data[user_num]['id'],  # User who needs to pick from pack
                    'pack_num': pack_num,  # Order of pack opening
                    'picked_ids': [],
                    'events': [],
                    'opened': False,
                })

        setup.update(more_setup)
        return included_card_data

    @staticmethod
    def rotisserie(setup: dict, user_data: list):
        cube = Cube.query.get(setup['cube_id'])
        wrapper = CubeWrapper(cube)
        card_data = wrapper.card_data(include_removed=False)

        first_pick_id = random.choice(user_data)['id']

        setup.update({
            'card_ids': [str(x) for x in card_data.keys()],
            'waiting_id': first_pick_id,
            'picked_ids': [],
            'events': [],
        })
        return card_data

    @staticmethod
    def _basic_land_pool():
        cube = Cube.query.filter(Cube.name == 'basic lands').first()
        cards = CubeCard.query.filter(
            CubeCard.cube_id == cube.id,
            CubeCard.id == CubeCard.latest_id,
            CubeCard.name_tmp.in_((
                'Forest',
                'Island',
                'Swamp',
                'Mountain',
                'Plains',
            )),
        ).all()

        return cards


    @staticmethod
    def _make_set_pack(pools, distribution):
        # Shuffle all of the pools
        for pool in pools.values():
            random.shuffle(pool)

        cards = []
        card_data = {}

        for pool_name, count in distribution:
            cards += pools[pool_name][:count]
            for card in cards:
                card_data[card.id] = card.get_json()

        card_ids = [x.id for x in cards]

        return card_ids, card_data

    @staticmethod
    def _make_set_packs(cube_id, count):
        pools, distribution = RoundBuilder._make_pack_slot_pools(cube_id)

        packs = []
        included_card_data = {}

        for _ in range(count):
            ids, card_data = RoundBuilder._make_set_pack(pools, distribution)
            packs.append(ids)
            included_card_data.update(card_data)

        return packs, included_card_data

    @staticmethod
    def _make_pack_slot_pools(cube_id):
        cube = Cube.query.get(cube_id)
        wrapper = CubeWrapper(cube)
        set_code = cube.set_code.lower() if cube.set_code else 'other'

        pools = {
            'all': wrapper.cards(),
            'rare': [],
            'uncommon': [],
            'common': [],
            'basic-land': RoundBuilder._basic_land_pool(),
        }

        distribution = [
            ('rare', 1),
            ('uncommon', 3),
            ('common', 10),
            ('basic-land', 1),
        ]

        # Special distributions/pools for some sets.

        if set_code == 'khm':
            pools['snow-land'] = []

        elif set_code in ('isd', 'dka'):
            pools['double-faced'] = []
            distribution = [
                ('rare', 1),
                ('double-faced', 1),
                ('uncommon', 3),
                ('common', 9),
            ]

        # Build pools

        for card in pools['all']:
            if set_code == 'khm' and 'snow land' in card.type_line().lower():
                # One pack in six should have a snow dual.
                # Since there are ten snow duals, have 10 of each basic to make the ratios right.
                if 'basic' in card.type_line().lower():
                    pools['snow-land'] += [card] * 10
                else:
                    pools['snow-land'].append(card)

            elif 'double-faced' in pools and '//' in card.name():
                # Need to get the distribution right for rarity.
                # There is 1 of each mythic for every 2 of each rare
                # There is 1 of each rare for every 3 of each uncommon
                # There is 1 of each rare for every 11 of each common
                if card.rarity() == 'mythic':
                    pools['double-faced'].append(card)
                elif card.rarity() == 'rare':
                    pools['double-faced'] += [card] * 2
                elif card.rarity() == 'uncommon':
                    pools['double-faced'] += [card] * 6
                elif card.rarity() == 'common':
                    pools['double-faced'] += [card] * 22
                else:
                    raise ValueError(f"Unknown rarity '{card.rarity()}' on '{card.name()}'")
            elif card.rarity() == 'mythic':
                pools['rare'].append(card)
            elif card.rarity() == 'rare':
                pools['rare'].append(card)
                pools['rare'].append(card)  # Mythics are twice as rare as regular rares
            elif card.rarity() == 'uncommon':
                pools['uncommon'].append(card)
            elif card.rarity() == 'common':
                pools['common'].append(card)
            else:
                raise ValueError(f"Unknown rarity '{card.rarity()}' on '{card.name()}'")

        return pools, distribution
