import random

from app import db
from app.models import Card
from app.models import Draft
from app.models import Pack
from app.models import PackCard
from app.models import Participant
from app.models import User


class DraftWrapper(object):
    def __init__(self, draft_id, user):
        self.draft = Draft.query.get(draft_id)
        self.user = user
        self.participant = next(x for x in self.draft.participants if x.user_id == user.id)
        self.pack = self.participant.waiting_pack()
        self.pack_cards = [x for x in self.pack.cards if not x.picked()] if self.pack else None
        self.picks = PackCard.query.filter(
            PackCard.draft_id==draft_id,
            PackCard.picked_by_id==self.participant.id,
        ).all()

    def pick_card(self, card_id):
        pack_card = PackCard.query.filter(PackCard.id==card_id).first()
        pack_card.picked_by = self.participant
        pack_card.pick_number = self.pack.num_picked + 1
        db.session.add(pack_card)
        
        self.pack.num_picked += 1
        db.session.add(self.pack)
        db.session.commit()


def create_draft(
        name: str,
        participants: list,  # List of usernames
        pack_size: int,
        num_packs: int,
):
    draft = Draft(
        name=name,
        complete=False,
        pack_size=pack_size,
        num_packs=num_packs,
        num_seats=len(participants),
    )
    db.session.add(draft)

    random.shuffle(participants)
    for seat, p in enumerate(participants):
        user = User.query.filter(User.username==p).first()
        p_orm = Participant(
            user=user,
            draft=draft,
            seat=seat,
        )
        db.session.add(p_orm)

    for i, pack in enumerate(_make_packs(pack_size, num_packs, len(participants))):
        pack_number = i % num_packs
        seat_number = i // num_packs
        
        pack_orm = Pack(
            draft=draft,
            seat_number=seat_number,
            pack_number=pack_number,
        )
        db.session.add(pack_orm)

        for card in pack:
            pc = PackCard(
                card=card,
                draft=draft,
                pack=pack_orm,
            )
            db.session.add(card)
        
    db.session.commit()


def _make_packs(pack_size, num_packs, num_players):
    cards = Card.query.all()
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
