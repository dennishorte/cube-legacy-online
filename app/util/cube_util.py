from app import db
from app.models.cube_models import *
from app.util import scryfall


def add_cards_to_cube(cube_id, card_names, added_by, comment):
    comment = comment.strip()

    _ensure_cube(cube_id)
    scryfall_data = scryfall.fetch_many_from_scryfall(card_names)
    failed_to_fetch = []

    for name, datum in list(scryfall_data.items()):
        if datum is None or datum['object'] == 'error':
            failed_to_fetch.append(name)
            del scryfall_data[name]
        else:
            scryfall.convert_to_clo_standard_json(datum)

    _create_base_cards_from_scryfall_data(scryfall_data)

    true_names_with_dups = []
    for name in card_names:
        if name in scryfall_data:
            true_names_with_dups.append(scryfall_data[name]['name'])

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

    return {
        'num_added': len(true_names_with_dups),
        'num_unique_added': len(base_cards),
        'failed_to_fetch': failed_to_fetch,
    }


def _ensure_cube(cube_id):
    cube = Cube.query.get(cube_id)
    if not cube:
        raise ValueError("Invalid cube id: {}".format(cube_id))

    return cube


def _create_base_cards_from_scryfall_data(data: dict):
    true_names = [x['name'] for x in data.values()]

    existing_cards = BaseCard.query.filter(BaseCard.name.in_(true_names))
    existing_names = set([x.name for x in existing_cards])

    for scryfall_datum in data.values():
        if scryfall_datum and scryfall_datum['name'] not in existing_names:
            bc = BaseCard(name=scryfall_datum['name'])
            bc.set_json(scryfall_datum)
            db.session.add(bc)

    db.session.commit()
