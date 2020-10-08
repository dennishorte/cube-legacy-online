import requests
import time


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
