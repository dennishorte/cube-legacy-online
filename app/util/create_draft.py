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
        scar_rounds: str,
        pack_maker = None,
        picks_per_pack = 1,
):
    cube = Cube.query.filter(Cube.name == cube_name).first()

    draft = Draft(
        name=name,
        cube_id=cube.id,
        pack_size=pack_size,
        num_packs=num_packs,
        num_seats=len(user_names),
        scar_rounds_str=scar_rounds,
        picked_per_pack=picked_per_pack,
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

    if not pack_maker:
        pack_maker = _make_cube_packs

    packs = pack_maker(cube, pack_size, num_packs, len(users))

    for i, cube_cards_for_pack in enumerate(packs):
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


def create_set_draft(
        name: str,
        cube_name: str,
        style: str,
        user_names: list,
):
    if style == 'commander':
        pack_size = 20
        pack_maker = _make_commander_packs
        picks_per_pack = 2
    else:
        pack_size = 15
        pack_maker = _make_set_packs
        picks_per_pack = 1

    create_draft(
        name = name,
        cube_name = cube_name,
        pack_size = pack_size,
        num_packs = 3,
        user_names = user_names,
        scar_rounds = '',
        pack_maker = pack_maker,
        picks_per_pack = picks_per_pack,
    )


def _make_cube_packs(cube, pack_size, num_packs, num_players):
    cards = cube.cards()

    total_cards = pack_size * num_packs * num_players
    total_packs = num_packs * num_players

    if len(cards) < total_cards:
        raise ValueError("Not enough cards ({}) for {} packs of size {} and {} players.".format(
            len(cards), num_packs, pack_size, num_players))

    random.shuffle(cards)
    packs = []
    for i in range(total_packs):
        start = i * pack_size
        end = start + pack_size
        packs.append(cards[start:end])

    return packs  # List of list of Card ORMs


def _make_commander_packs(cube, unused, num_packs, num_players):
    card_breakdown = {
        'all': cube.cards(),
        'rare': [],  # mythics get shuffled in here
        'uncommon': [],
        'common': [],
        'legendary': [],  # All the legendary creatures
    }

    distribution = [
        ('rare', 1),
        ('uncommon', 3),
        ('legendary', 2),
        ('common', 13),
        ('all', 1),  # Foil
    ]

    for card in card_breakdown['all']:
        if 'legendary creature' in card.type_line().lower():
            card_breakdown['legendary'].append(card)
        elif card.rarity() in ('rare', 'mythic'):
            card_breakdown['rare'].append(card)
        elif card.rarity() == 'uncommon':
            card_breakdown['uncommon'].append(card)
        elif card.rarity() == 'common':
            card_breakdown['common'].append(card)
        else:
            raise ValueError(f"Unknown rarity '{card.rarity()}' on '{card.name()}'")

    return _make_set_packs(card_breakdown, distribution, num_packs * num_players)


def _make_standard_packs(cube, unused, num_packs, num_players):
    card_breakdown = {
        'all': cube.cards(),
        'rare': [],  # mythics get shuffled in here
        'uncommon': [],
        'common': [],
    }

    distribution = [
        ('rare', 1),
        ('uncommon', 3),
        ('common', 10),
    ]

    for card in card_breakdown['all']:
        if card.rarity() in ('rare', 'mythic'):
            card_breakdown['rare'].append(card)
        elif card.rarity() == 'uncommon':
            card_breakdown['uncommon'].append(card)
        elif card.rarity() == 'common':
            card_breakdown['common'].append(card)
        else:
            raise ValueError(f"Unknown rarity '{card.rarity()}' on '{card.name()}'")

    return _make_set_packs(card_breakdown, distribution, num_packs * num_players)


def _make_set_packs(card_breakdown, distribution, total_packs):
    packs = []
    for _ in range(total_packs):
        for card_list in card_breakdown.values():
            random.shuffle(card_list)

        cards = []
        for rarity, count in distribution:
            cards += card_breakdown[rarity][:count]

        packs.append(cards)

    return packs
