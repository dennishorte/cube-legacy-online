import random
from datetime import datetime

from app import db
from app.util import admin_util


def cull_sideboard(deck, ratio, comment):
    """
    ratio is in the form of a decimal between zero and one, where one will cull all cards.
    """
    cards = deck.sideboard()
    random.shuffle(cards)

    cull_count = int(len(cards) * ratio)
    starter_user = admin_util.starter_user()
    will_remove = cards[:cull_count]

    for card in will_remove:
        card.removed_by_id = starter_user.id
        card.removed_by_comment = comment or "culled from sideboard"
        card.removed_by_timestamp = datetime.utcnow()
        db.session.add(card)

    db.session.commit()

    return will_remove
