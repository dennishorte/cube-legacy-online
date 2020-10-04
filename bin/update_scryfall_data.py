import os
os.environ['FLASK_ENV'] = 'development'


import json
import requests
import time

from app import db
from app.models import *


def fetch_one_from_scryfall(card_name):
    params = {'fuzzy': card_name}
    r = requests.get('http://api.scryfall.com/cards/named?fuzzy=', params=params)
    return r.json()


def extract_card_image(scryfall_json):
    if 'image_uris' in scryfall_json:
        card_img = scryfall_json['image_uris']['normal']

    elif 'card_faces' in scryfall_json:
        imgs = [x['image_uris']['normal'] for x in scryfall_json['card_faces']]
        card_img=','.join(imgs)

    else:
        print('+++ No image_uris for: {}'.format(card_name))
        card_img = None

    return card_img


def update_one(scryfall_json, card_name, fix_names=False):
    scryfall_name = scryfall_json['name']

    card_img = extract_card_image(scryfall_json)
    if card_img:
        cards = Card.query.filter(Card.name == card_name).all()
        for card in cards:
            if fix_names and card_name != scryfall_name:
                print("... ...fixing name of {} to {}".format(card_name, scryfall_name))
                card.name=scryfall_name
            card.image_url=card_img
            db.session.add(card)
        

    scryfall_data = ScryfallData.query.filter(ScryfallData.name == scryfall_name).first()

    if scryfall_data:
        scryfall_data.json = json.dumps(scryfall_json)
        db.session.add(scryfall_data)

    else:
        scryfall_data = ScryfallData(
            name=scryfall_name,
            json=json.dumps(scryfall_json)
        )
        db.session.add(scryfall_data)

    db.session.commit()


def get_all_card_names():
    print('Get all card names')
    all_card_names = [x.name for x in Card.query.all()]
    unique_card_names = list(set(all_card_names))
    print('...got {} ({} duplicates filtered)'.format(
        len(unique_card_names),
        len(all_card_names) - len(unique_card_names),
    ))

    for card_name in unique_card_names:
        all_card_names.remove(card_name)

    for card_name in all_card_names:
        print('...duplicate: {}'.format(card_name))
    
    return sorted(unique_card_names)


def get_card_names_missing_image_urls():
    print('Get card names missing image urls')

    all_card_names = [x.name for x in Card.query.filter(Card.image_url == None).all()]
    unique_card_names = list(set(all_card_names))
    print('...got {} ({} duplicates filtered)'.format(
        len(unique_card_names),
        len(all_card_names) - len(unique_card_names),
    ))

    for card_name in unique_card_names:
        all_card_names.remove(card_name)

    for card_name in all_card_names:
        print('...duplicate: {}'.format(card_name))
    
    return sorted(unique_card_names)


def fetch_each_and_update(card_names, fix_names=False):
    print('Fetch each and update')
    print('...expected time to completion = {} seconds'.format(.1 * len(card_names)))
    
    for card_name in card_names:
        existing = ScryfallData.query.filter(ScryfallData.name == card_name).first()
        if existing:
            if fix_names:
                print('...reusing  {}'.format(card_name))
                scryfall_json = json.loads(existing.json)
            else:
                continue
        else:
            print('...fetching {}'.format(card_name))
            scryfall_json = fetch_one_from_scryfall(card_name)

        if scryfall_json:
            update_one(scryfall_json, card_name, fix_names)
        else:
            print('... ...failure')

        time.sleep(.080)  # 80 ms delay, as requested by scryfall


def update_all_scryfall_data():
    print('Update all scryfall data')

    card_names = get_all_card_names()
    # card_names = get_card_names_missing_image_urls()
    fetch_each_and_update(
        card_names,
        fix_names = False,
    )


if __name__ == "__main__":
    update_all_scryfall_data()
