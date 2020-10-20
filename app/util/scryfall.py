import requests
import time
from copy import deepcopy

from app.util.card_util import CardConsts


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
    _convert_image_storage(card_json)
    _convert_to_face_array(card_json)
    _convert_remove_unwanted_root_keys(card_json)
    _convert_remove_unwanted_face_keys(card_json)
    _convert_ensure_all_root_keys(card_json)
    _convert_ensure_all_face_keys(card_json)
    _convert_build_combined_oracle_text(card_json)
    

def _convert_to_face_array(card_json):
    # If the card has no card_faces, make one out of the singleton face.
    if not 'card_faces' in card_json:
        face_json = {}
        card_json['card_faces'] = [face_json]

        for key in CardConsts.FACE_KEYS:
            if key in card_json:
                face_json[key] = card_json[key]

    # Special case for flip cards. Technically, the same image, so scryfall puts it in the root.
    elif 'image_url' in card_json:
        for face in card_json['card_faces']:
            face['image_url'] = card_json['image_url']

        del card_json['image_url']


def _convert_image_storage(card_json):
    all_parts = [card_json] + card_json.get('card_faces', [])
    
    for face in all_parts:
        if 'image_uris' in face:
            face['image_url'] = face['image_uris']['normal']
            del face['image_uris']


def _convert_remove_unwanted_root_keys(card_json):
    for key in list(card_json.keys()):
        if key not in CardConsts.ROOT_KEYS:
            del card_json[key]

            
def _convert_remove_unwanted_face_keys(card_json):
    for face in card_json['card_faces']:
        for key in list(face.keys()):
            if key not in CardConsts.FACE_KEYS:
                del face[key]

                
def _convert_ensure_all_root_keys(card_json):
    for key in CardConsts.ROOT_KEYS:
        if key not in card_json:
            card_json[key] = ''
        

def _convert_ensure_all_face_keys(card_json):
    for face in card_json['card_faces']:
        for key in CardConsts.FACE_KEYS:
            if key not in face:
                face[key] = ''
        

def _convert_build_combined_oracle_text(card_json):
    each_oracle_text = []
    for face in card_json['card_faces']:
        each_oracle_text.append(face.get('oracle_text'))

    each_oracle_text = [x for x in each_oracle_text if x]
    card_json['oracle_text'] = '\n-----\n'.join(each_oracle_text)
