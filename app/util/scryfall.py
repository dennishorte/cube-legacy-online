import requests
import time
from copy import deepcopy


class CardConsts(object):
    JSON_KEYS = (
        # Meta data
        'all_parts',
        'card_faces',
        'layout',
        'object',

        # Card data
        'cmc',
        'component',
        'flavor_text',
        'image_url',
        'loyalty',
        'mana_cost',
        'name',
        'oracle_text',
        'power',
        'toughness',
        'type_line',
    )

    FACE_KEYS = (
        'flavor_text',
        'loyalty',
        'mana_cost',
        'name',
        'object',
        'oracle_text',
        'power',
        'toughness',
        'type_line',
    )

    COMBINING_KEYS = (
        'name',
        'type_line',
        'oracle_text',
    )


def fetch_one_from_scryfall(card_name):
    params = {'fuzzy': card_name}
    r = requests.get('http://api.scryfall.com/cards/named?fuzzy=', params=params)
    return r.json()


def fetch_many_from_scryfall(card_names: list):
    """
    Returns a dict of {card_name: scryfall_json}.
    Because the fetch function uses fuzzy name matching, the card names don't have to
    be perfect in order to fetch the data. For the same reasons, the card names in the
    scryfall json might not match the card name used as the key in the returned dict.
    """
    results = {}

    print("Fetching {} cards from Scryfall".format(len(card_names)))
    
    for i, name in enumerate(card_names):
        print("...{} of {}: {}".format(i, len(card_names), name))
        results[name] = fetch_one_from_scryfall(name)
        time.sleep(.100)  # 100 ms delay, as requested by scryfall

    print("...COMPLETE (fetching cards from Scryfall")

    return results


def convert_to_clo_standard_json(card_json):
    card_json = deepcopy(card_json)

    _convert_to_face_array(card_json)
    _convert_image_storage(card_json)
    _convert_remove_unwanted_keys(card_json)

    return card_json


def _convert_to_face_array(card_json):
    # If the card has no card_faces, make one out of the singleton face.
    if not 'card_faces' in card_json:
        face_json = {}
        card_json['card_faces'] = face_json

        for key in CardConsts.FACE_KEYS:
            if key in card_json:
                face_json[key] = card_json[key]

            if key not in CardConsts.COMBINING_KEYS:
                del card_json[key]


def _convert_image_storage(card_json):
    for face in card_json['card_faces']:
        face['image_url'] = face['image_uris']['normal']
        del face['image_uris']


def _convert_remove_unwanted_keys(card_json):
    all_parts = [card_json] + card_json['card_faces']
    for part in all_parts:
        for key in CardConsts.JSON_KEYS:
            if key in part:
                del part[key]
