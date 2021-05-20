import random

from app.util.cube_wrapper import CubeWrapper


def make_packs(
        cube,
        style: str,
        pack_size: int,
        num_packs: int = 0,
):
    if style == 'cube':
        return make_cube_packs(cube, pack_size, num_packs)
    elif style == 'set':
        return make_set_packs(cube, num_packs)


def make_cube_packs(cube, pack_size, num_packs):
    cube_wrapper = CubeWrapper(cube)
    cards = cube_wrapper.cards()

    if len(cards) < pack_size * num_packs:
        raise ValueError("Not enough cards ({}) for {} packs of size {}.".format(
            len(cards), num_packs, pack_size))

    random.shuffle(cards)

    packs = []
    for i in range(num_packs):
        start = i * pack_size
        end = start + pack_size
        packs.append([x.id for x in cards[start:end]])

    return packs  # List of list of card ids


def make_set_packs(cube, num_packs):
    card_breakdown, distribution = _get_distribution_for_set(cube)

    packs = []
    for _ in range(num_packs):
        for card_list in card_breakdown.values():
            random.shuffle(card_list)

        cards = []
        for rarity, count in distribution:
            cards += card_breakdown[rarity][:count]

        packs.append([x.id for x in cards])

    return packs


def _get_distribution_for_set(cube):
    set_code = cube.set_code.lower()

    card_breakdown = {
        'all': [],
        'rare': [],  # mythics get shuffled in here
        'uncommon': [],
        'common': [],
    }

    if set_code == 'cmr':
        card_breakdown['legendary'] = []
        distribution = [
            ('rare', 1),
            ('uncommon', 3),
            ('legendary', 2),
            ('common', 13),
            ('all', 1),  # Foil
        ]

    elif set_code in ('isd', 'dka'):
        card_breakdown['double-faced'] = []
        distribution = [
            ('rare', 1),
            ('uncommon', 3),
            ('double-faced', 1),
            ('common', 9),
        ]

    elif set_code == 'khm':
        card_breakdown['snow-land'] = []
        distribution = [
            ('rare', 1),
            ('uncommon', 3),
            ('common', 10),
            ('snow-land', 1),
        ]

    else:
        distribution = [
            ('rare', 1),
            ('uncommon', 3),
            ('common', 10),
        ]

    _fill_breakdown(cube, card_breakdown)

    return card_breakdown, distribution


def _fill_breakdown(cube, card_breakdown):
    cube_wrapper = CubeWrapper(cube)

    card_breakdown['all'] = cube_wrapper.cards()


    for card in card_breakdown['all']:
        if 'snow-land' in card_breakdown and 'snow land' in card.type_line().lower():
            # One pack in six should have a snow dual.
            # Since there are ten snow duals, have 10 of each basic to make the ratios right.
            if 'basic' in card.type_line().lower():
                card_breakdown['snow-land'] += [card] * 10
            else:
                card_breakdown['snow-land'].append(card)

        elif 'legendary' in card_breakdown and 'legendary creature' in card.type_line().lower():
            card_breakdown['legendary'] += [card] * _rarity_multiplier(card.rarity())

        elif 'double-faced' in card_breakdown and '//' in card.name():
            card_breakdown['double-faced'] += [card] * _rarity_multiplier(card.rarity())

        elif card.rarity() == 'mythic':
            card_breakdown['rare'].append(card)
        elif card.rarity() == 'rare':
            card_breakdown['rare'].append(card)
            card_breakdown['rare'].append(card)  # Mythics are twice as rare as regular rares
        elif card.rarity() == 'uncommon':
            card_breakdown['uncommon'].append(card)
        elif card.rarity() == 'common':
            card_breakdown['common'].append(card)
        else:
            raise ValueError(f"Unknown rarity '{card.rarity()}' on '{card.name()}'")


def _rarity_multiplier(rarity):
    mapping = {
        'mythic': 1,
        'rare': 2,
        'uncommon': 3,
        'common': 10,
    }
    return mapping[rarity]
