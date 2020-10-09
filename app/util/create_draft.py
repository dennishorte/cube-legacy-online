import random

from app.models.cube import *
from app.models.draft import *
from app.models.user import *


def create_draft(
        name: str,
        cube_name: str,
        pack_size: int,
        num_packs: int,
        user_names: list,
):
    cube = Cube.query.filter(Cube.name == cube_name).first()
    
    draft = Draft(
        name=name,
        cube_id=cube.id,
        pack_size=pack_size,
        num_packs=num_packs,
        num_seats=len(user_names),
    )
    db.session.add(draft)

    users = User.query.filter(User.name.in_(user_names)).all()
    random.shuffle(users)
    for index, user in enumerate(users):
        seat = Seat(
            order=index,
            user_id=user.id,
            draft_id=draft.id,
        )
        db.session.add(seat)

    for i, cube_cards_for_pack in enumerate(_make_packs(cube, pack_size, num_packs, len(users))):
        pack_number = i % num_packs
        seat_number = i // num_packs
        
        pack = Pack(
            draft=draft,
            seat_number=seat_number,
            pack_number=pack_number,
        )
        db.session.add(pack)

        for card in cube_cards_for_pack:
            pc = PackCard(
                card_id=card.id,
                draft=draft,
                pack=pack,
            )
            db.session.add(card)
        
    db.session.commit()


def _make_packs(cube, pack_size, num_packs, num_players):
    cards = CubeCard.query.filter(
        CubeCard.cube_id == cube.id,
        CubeCard.latest == True,
    ).all()
    
    total_cards = pack_size * num_packs * num_players
    total_packs = num_packs * num_players

    if len(cards) < total_cards:
        raise ValueError("Not enough cards ({}) for {} packs of size {} and {} players.".format(
            len(cards), num_packs, pack_size, num_players))

    random.shuffle(cards)
    cards = cards[:total_cards]
    packs = []
    for i in range(total_packs):
        start = i * pack_size
        end = start + pack_size
        packs.append(cards[start:end])

    return packs  # List of list of Card ORMs
