from app import db
from app.models.cube_models import *
from app.util import admin_util
from app.util import scryfall


def create_set_cube(set_code):
    # Get the set info from Scryfall
    set_info = scryfall.fetch_set_info(set_code)
    set_name = set_info['name']

    # Get the card info from Scryfall
    scryfall_cards = scryfall.fetch_set_cards(set_code, set_info['card_count'])
    print(f"Fetched {len(scryfall_cards)} cards for set {set_name}")

    # If two cards have the same name, keep only the one with the lower set number
    name_to_data = {}
    for card in scryfall_cards:
        use_card = True

        if card['name'] in name_to_data:
            this_id = int(card['collector_number'])
            other_id = int(name_to_data[card['name']]['collector_number'])

            if this_id > other_id:
                use_card = False

        if use_card:
            name_to_data[card['name']] = card

    scryfall_cards = list(name_to_data.values())

    # Convert the Scryfall json to CLO json
    for card_json in scryfall_cards:
        scryfall.convert_to_clo_standard_json(card_json)

    # Create the cube
    cube = Cube()
    cube.name = 'Set: ' + set_name
    cube.style_a = 'set'
    cube.set_code = set_code
    db.session.add(cube)
    db.session.commit()

    starter_user = admin_util.starter_user()

    for card_json in scryfall_cards:
        if card_json['name'] in ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest']:
            continue

        card = CubeCard()
        card.cube_id = cube.id
        card.added_by = starter_user
        card.version = 1
        card.set_json(card_json)
        db.session.add(card)
    db.session.commit()

    # Give all the new cards a group id.
    for c in cube._cards:
        c.latest_id = c.id
        db.session.add(c)
    db.session.commit()


def add_cards_to_cube(cube_id, card_names, added_by, comment):
    comment = comment.strip()

    _ensure_cube(cube_id)
    scryfall_data = scryfall.fetch_many_from_scryfall(card_names)

    # Convert the Scryfall json to CLO json
    for card_json in scryfall_data:
        scryfall.convert_to_clo_standard_json(card_json)

    _create_base_cards_from_scryfall_data(scryfall_data)

    true_names_with_dups = [x['name'] for x in scryfall_data]
    base_cards = BaseCard.query.filter(BaseCard.name.in_(true_names_with_dups)).all()
    base_card_map = {x.name: x for x in base_cards}

    new_cards = []
    for true_name in true_names_with_dups:
        base_card = base_card_map[true_name]
        cc = CubeCard.from_base_card(
            base_card=base_card,
            cube_id=cube_id,
            added_by=added_by,
        )
        if comment:
            cc.comment = comment
        new_cards.append(cc)
        db.session.add(cc)

    db.session.commit()

    # Give all the new cards a group id.
    for c in new_cards:
        c.latest_id = c.id
        db.session.add(c)
    db.session.commit()


def remove_cards_from_cube(cube_id, card_names, removed_by, comment):
    if not card_names:
        return

    card_names = [x.lower() for x in card_names]
    comment = comment.strip()
    _ensure_cube(cube_id)
    all_cards = CubeCard.query.filter(CubeCard.cube_id == cube_id).all()
    cards = [x for x in all_cards if x.name_tmp.lower() in card_names]

    for card in cards:
        card.removed_by_id = removed_by.id
        card.removed_by_comment = comment
        card.removed_by_timestamp = datetime.utcnow()
        db.session.add(card)

    db.session.commit()


def _ensure_cube(cube_id):
    cube = Cube.query.get(cube_id)
    if not cube:
        raise ValueError("Invalid cube id: {}".format(cube_id))

    return cube


def _create_base_cards_from_scryfall_data(data: list):
    true_names = [x['name'] for x in data]

    existing_cards = BaseCard.query.filter(BaseCard.name.in_(true_names))
    existing_names = set([x.name for x in existing_cards])

    for scryfall_datum in data:
        if scryfall_datum and scryfall_datum['name'] not in existing_names:
            bc = BaseCard(name=scryfall_datum['name'])
            bc.set_json(scryfall_datum)
            db.session.add(bc)

    db.session.commit()
