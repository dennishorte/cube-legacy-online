import difflib
import re


class CardConsts(object):
    ROOT_KEYS = (
        'card_faces',
        'cmc',
        'layout',
        'name',
        'object',
        'oracle_text',
        'rarity',
        'type_line',
    )

    FACE_KEYS = (
        'flavor_text',
        'image_url',
        'loyalty',
        'mana_cost',
        'name',
        'object',
        'oracle_text',
        'power',
        'toughness',
        'type_line',
    )

    CARD_TYPES = (
        'creature',
        'planeswalker',
        'sorcery',
        'instant',
        'artifact',
        'enchantment',
        'land',
    )

    MULTICOLOR_MAP = {
        'BG': 'Golgari',
        'BR': 'Rakdos',
        'BU': 'Dimir',
        'BW': 'Orzhov',
        'GR': 'Gruul',
        'GU': 'Simic',
        'GW': 'Selesnya',
        'RU': 'Izzet',
        'RW': 'Boros',
        'UW': 'Azorius',

        'BGR': 'Jund',
        'BGU': 'Sultai',
        'BGW': 'Abzan',
        'BRU': 'Grixis',
        'BRW': 'Mardu',
        'BUW': 'Esper',
        'GRU': 'Temur',
        'GRW': 'Naya',
        'GUW': 'Bant',
        'RUW': 'Jeskai',

        'BGRU': 'Non-White',
        'BGRW': 'Non-Blue',
        'BGUW': 'Non-Red',
        'BRUW': 'Non-Green',
        'GRUW': 'Non-Black',

        'BGRUW': '5-Color',
    }


def _ensure_rarity(data):
    if 'rarity' not in data:
        data['rarity'] = 'common'


def update_json_keys(card):
    """
    Utility for updating the card data when a new key is added.
    """
    data = card.get_json().copy()
    _ensure_rarity(data)
    return card.update(
        new_json = data,
        edited_by = None,
        comment = None,
        commit = False,
        new_version = False,
    )


def empty_card_json():
    return {
        'object': 'card',
        'cmc': '0',
        'card_faces': [],
    }


def color_sort_key(color_ch):
    ch = color_ch.upper()
    if ch.isnumeric():
        return 0
    elif ch == 'W':
        return 1
    elif ch == 'U':
        return 2
    elif ch == 'B':
        return 3
    elif ch == 'R':
        return 4
    elif ch == 'G':
        return 5
    else:
        return 6


def cmc_from_string(cost_string):
    cost = 0

    cost_string = cost_string.upper()
    pattern = r"{(.*?)}"
    for mana_symbol in re.findall(pattern, cost_string):
        if mana_symbol.isnumeric():
            cost += int(mana_symbol)

        elif mana_symbol.startswith('2/'):
            cost += 2

        elif mana_symbol in 'XYZ':
            pass

        else:
            cost += 1

    return cost
