"""
A place to put routes that are very specific to our own version of Cube Legacy.
"""

from datetime import datetime

from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required

from app import app
from app.forms import AddCardsForm
from app.forms import NewAchievementForm
from app.forms import NewCubeForm
from app.forms import NewScarForm
from app.forms import RandomScarsForm
from app.forms import UseScarForm
from app.models.cube_models import *
from app.models.draft_models import *
from app.models.user_models import *
from app.util.cube_util import add_cards_to_cube


@app.route('/cubes/<cube_id>/pack_of_dead_interns')
@login_required
def pack_of_dead_interns(cube_id):
    cube = Cube.query.get(cube_id)
    removed_cards = cube.cards_removed()
    interns = [x for x in removed_cards if 'intern of ' in x.get_json()['oracle_text'].lower()]

    return render_template(
        'pack_of_cards.html',
        title='Pack of Dead Interns',
        cards=interns,
    )
