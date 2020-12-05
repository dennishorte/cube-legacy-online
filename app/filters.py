from app import app
from app.models.draft_models import *


@app.template_filter()
def cube_cardify(card):
    if isinstance(card, PackCard):
        return card.cube_card
    else:
        return card
