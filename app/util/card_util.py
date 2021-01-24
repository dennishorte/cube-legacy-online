import difflib
import re

class CardConsts(object):
    RARITIES = (
        'common',
        'uncommon',
        'rare',
        'mythic',
    )

    RARITY_SHORT_FORMS = {
        'c': 'common',
        'u': 'uncommon',
        'r': 'rare',
        'm': 'mythic',
    }

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
        'art_crop_url',
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
        'other',
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


def empty_card_json():
    return {
        'object': 'card',
        'cmc': '0',
        'card_faces': [],
    }


def cards_by_id(card_ids: list):
    from app.models.cube_models import CubeCard

    card_ids = [int(x) for x in card_ids]
    cards = CubeCard.query.filter(CubeCard.id.in_(card_ids)).all()

    # Let the user know if any cards weren't able to be added.
    id_set = set(card_ids)
    card_set = set([x.id for x in cards])
    missing = list(id_set - card_set)

    return {
        'cards': cards,
        'missing': missing,
    }


def card_by_name(card_name):
    from app.models.cube_models import Cube
    from app.models.cube_models import CubeCard
    from app.util import admin_util
    from app.util.cube_util import add_cards_to_cube

    # See if it exists in any active cube.
    cards = CubeCard.query.join(CubeCard.cube).filter(
        CubeCard.name_tmp == card_name,
        CubeCard.id == CubeCard.latest_id,
        Cube.admin == False,
    ).all()

    if cards:
        return cards

    # Finally, see if we can grab it from Scryfall.
    starter_user = admin_util.starter_user()
    scryfall_cube = admin_util.scryfall_cube()

    scryfall_card = CubeCard.query.filter(
        CubeCard.cube_id == scryfall_cube.id,
        CubeCard.name_tmp == card_name,
        CubeCard.id == CubeCard.latest_id,
    ).first()

    if scryfall_card:
        return [scryfall_card]

    result = add_cards_to_cube(
        scryfall_cube.id,
        [card_name],
        starter_user,
        "Dynamic fetch for get card by name",
    )

    if result['num_added'] == 1:
        return CubeCard.query.filter(
            CubeCard.cube_id == scryfall_cube.id,
            CubeCard.name_tmp == card_name,
        ).all()
    else:
        return []


def cards_by_name(card_names: list):
    cards = []
    missing = []
    multiples = []

    for name in card_names:
        card = card_by_name(name)
        if len(card) == 0:
            missing.append(name)
        elif len(card) == 1:
            cards.append(card[0])
        else:
            multiples.append(card)

    return {
        'cards': cards,
        'missing': missing,
        'multiples': multiples,
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
