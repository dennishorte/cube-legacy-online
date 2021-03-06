import random

from app import app
from app.models.cube_models import *
from app.models.draft_models import *
from app.models.user_models import *
from app.util import slack
from app.util.cube_wrapper import CubeWrapper


def create_draft(
        name: str,
        cube_name: str,
        pack_size: int,
        num_packs: int,
        user_names: list,
        scar_rounds: str,
        pack_maker = None,
        picks_per_pack = 1,
        parent_id = None,
):
    if parent_id == '0':
        parent_id = None

    if parent_id:
        parent_id = int(parent_id)
        parent_draft = Draft.query.get(parent_id)
        if not parent_draft:
            raise RuntimeError(f"Unable to link to draft {parent_id}")

    cube = Cube.query.filter(Cube.name == cube_name).first()

    draft = Draft(
        name=name,
        cube_id=cube.id,
        pack_size=pack_size,
        num_packs=num_packs,
        num_seats=len(user_names),
        scar_rounds_str=scar_rounds,
        picks_per_pack=picks_per_pack,
        parent_id=parent_id,
    )
    db.session.add(draft)

    users = User.query.filter(User.name.in_(user_names)).all()
    if parent_id:
        if sorted([x.id for x in users]) != sorted([x.user_id for x in parent_draft.seats]):
            raise RuntimeError(f"Can't link drafts with different users")

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

    if app.config['FLASK_ENV'] == 'production':
        slack.send_new_draft_notifications(draft)


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
        pack_size = 14
        pack_maker = _make_standard_packs
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
    cube_wrapper = CubeWrapper(cube)
    cards = cube_wrapper.cards()

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
    cube_wrapper = CubeWrapper(cube)
    card_breakdown = {
        'all': cube_wrapper.cards(),
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
    cube_wrapper = CubeWrapper(cube)

    card_breakdown = {
        'all': cube_wrapper.cards(),
        'rare': [],  # mythics get shuffled in here
        'uncommon': [],
        'common': [],
    }

    distribution = [
        ('rare', 1),
        ('uncommon', 3),
        ('common', 10),
    ]

    separate_double_faced = False

    # These sets replaced one common slot with a double-faced card of any rarity.
    if cube.set_code.lower() in ('isd', 'dka'):
        separate_double_faced = True
        card_breakdown['double-faced'] = []
        distribution = [
            ('rare', 1),
            ('uncommon', 3),
            ('double-faced', 1),
            ('common', 9),
        ]

    if cube.set_code.lower() == 'khm':
        distribution.append(('snow-land', 1))
        card_breakdown['snow-land'] = []


    for card in card_breakdown['all']:
        if cube.set_code.lower() == 'khm' and 'snow land' in card.type_line().lower():
            # One pack in six should have a snow dual.
            # Since there are ten snow duals, have 10 of each basic to make the ratios right.
            if 'basic' in card.type_line().lower():
                card_breakdown['snow-land'] += [card] * 10
            else:
                card_breakdown['snow-land'].append(card)

        elif separate_double_faced and '//' in card.name():
            # Need to get the distribution right for rarity.
            if card.rarity() == 'mythic':
                card_breakdown['double-faced'].append(card)
            elif card.rarity() == 'rare':
                card_breakdown['double-faced'] += [card] * 7
            elif card.rarity() == 'uncommon':
                card_breakdown['double-faced'] += [card] * 24
            elif card.rarity() == 'common':
                card_breakdown['double-faced'] += [card] * 88
            else:
                raise ValueError(f"Unknown rarity '{card.rarity()}' on '{card.name()}'")
        elif card.rarity() == 'mythic':
            card_breakdown['rare'].append(card)
        elif card.rarity() == 'rare':
            card_breakdown['rare'].append(card)
            card_breakdown['rare'].append(card)  # Mythics are twice as rare as regular rares
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
