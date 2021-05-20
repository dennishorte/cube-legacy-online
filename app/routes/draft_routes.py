import json
import os
from datetime import datetime
from random import random

from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import login_required
from flask_login import logout_user

from app import app
from app.forms import *
from app.models.cube_models import *
from app.models.deck_models import *
from app.models.draft_models import *
from app.models.user_models import *
from app.util import cockatrice
from app.util import cull_util
from app.util.card_util import empty_card_json
from app.util.deck_builder import DeckBuilder
from app.util.draft_debugger import DraftDebugger
from app.util.draft_wrapper import DraftWrapper
from app.util.string import normalize_newlines


class NewDraftForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    cube = SelectField('Cube', validators=[DataRequired()])
    packsize = IntegerField('Pack Size', validators=[DataRequired()])
    numpacks = IntegerField('Number of Packs', validators=[DataRequired()])
    scar_rounds = StringField('Scar Rounds (eg. 0,3)')
    players = SelectMultipleField('Players', validators=[DataRequired()])
    parent = SelectField('Parent')
    submit = SubmitField('Create')

    @staticmethod
    def factory():
        from app.models.cube_models import Cube
        from app.models.draft_models import Draft
        from app.models.user_models import User

        cubes = [x.name for x in Cube.query.order_by('name')]
        users = [(x.name, x.name) for x in User.query.order_by('name') if x.name != 'starter']
        drafts = [(0, '')] + [(x.id, x.name) for x in Draft.query.order_by('name')]

        form = NewDraftForm()
        form.cube.choices = cubes
        form.players.choices = users
        form.parent.choices = drafts

        return form


class NewSetDraftForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    cube = SelectField('Cube', validators=[DataRequired()])
    style = SelectField('Style', validators=[DataRequired()], choices=['standard', 'commander'])
    players = SelectMultipleField('Players', validators=[DataRequired()])
    submit = SubmitField('Create')

    @staticmethod
    def factory():
        from app.models.cube_models import Cube
        from app.models.user_models import User

        cubes = [x.name for x in Cube.query.order_by('name') if x.style_a == 'set']
        users = [(x.name, x.name) for x in User.query.order_by('name') if x.name != 'starter']

        form = NewSetDraftForm()
        form.cube.choices = cubes
        form.players.choices = users

        return form


@app.route("/draft/<draft_id>")
@login_required
def draft(draft_id):
    dw = DraftWrapper(draft_id, current_user)
    dw._game_results_linked()
    return render_template('draft.html', d=dw)


@app.route("/draft/<draft_id>/cull_sideboards")
@login_required
def draft_cull_sideboards(draft_id):
    draft = Draft.query.get(draft_id)
    deck_links = DeckDraftLink.query.filter(DeckDraftLink.draft_id == draft_id).all()

    culled = {}

    for link in deck_links:
        culled[link.deck.user.name] = cull_util.cull_sideboard(
            link.deck,
            .5,
            f"Culled from sideboard during {draft.name}",
        )

    for key in culled:
        culled[key] = [x.name_tmp for x in culled[key]]

    return culled


@app.route("/draft/<draft_id>/debug")
@login_required
def draft_debug(draft_id):
    draft_debugger = DraftDebugger(draft_id)
    return render_template('draft_debug.html', d=draft_debugger)


@app.route("/draft/<draft_id>/deck_add_by_id/<card_id>")
@login_required
def draft_deck_add_card(draft_id, card_id):
    deck_builder = DeckBuilder(draft_id, current_user.id)
    deck = deck_builder.deck
    deck.add_card_by_id(card_id)
    db.session.add(deck)
    db.session.commit()

    return redirect(url_for('draft', draft_id=draft_id))


@app.route("/draft/<draft_id>/deck_save", methods=["POST"])
@login_required
def draft_deck_save(draft_id):
    data = request.json
    d = DeckBuilder(draft_id, current_user.id)

    maindeck = []
    for card_id in data['maindeck']:
        maindeck.append(CubeCard.query.get(card_id))
    d.deck.set_maindeck(maindeck)

    sideboard = []
    for card_id in data['sideboard']:
        sideboard.append(CubeCard.query.get(card_id))
    d.deck.set_sideboard(sideboard)

    command = []
    for card_id in data['command']:
        command.append(CubeCard.query.get(card_id))
    d.deck.set_command(command)

    basics = ','.join([x for x in data['basics'] if x[0] != '0'])
    d.deck.basic_lands = basics

    db.session.add(d.deck)
    db.session.commit()

    return 'success'


@app.route("/draft/<draft_id>/force/<user_id>")
@login_required
def draft_force(draft_id, user_id):
    user = User.query.get(user_id)
    dw = DraftWrapper(draft_id, user)

    # Pick the first card in the pack.
    if dw.pack:
        dw.seat.unlock_scars()
        dw.pick_card(dw.pack.unpicked_cards()[0].id)

    return redirect("/draft/{}".format(draft_id))


@app.route('/draft/next')
@login_required
def draft_next():
    next_drafts = current_user.drafts_waiting()
    if not next_drafts:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('draft', draft_id=next_drafts[0].id))


@app.route('/draft/new', methods=['POST'])
@login_required
def draft_new():
    form = NewDraftForm.factory()

    if form.validate_on_submit():
        from app.util.create_draft import create_draft
        create_draft(
            name=form.name.data,
            cube_name=form.cube.data,
            pack_size=form.packsize.data,
            num_packs=form.numpacks.data,
            user_names=form.players.data,
            scar_rounds=form.scar_rounds.data,
            parent_id=form.parent.data,
        )
        return redirect(url_for('index'))

    else:
        return "Unable to create new draft"


@app.route('/draft/new_set', methods=['POST'])
@login_required
def draft_new_set():
    form = NewSetDraftForm.factory()

    if form.validate_on_submit():
        from app.util.create_draft import create_set_draft
        create_set_draft(
            name=form.name.data,
            cube_name=form.cube.data,
            style=form.style.data,
            user_names=form.players.data,
        )
        return redirect(url_for('index'))

    else:
        return "Unable to create new draft"


@app.route("/draft/<draft_id>/kill")
@login_required
def draft_kill(draft_id):
    draft = Draft.query.get(draft_id)
    draft.killed = True
    db.session.add(draft)
    db.session.commit()

    return redirect(url_for('index'))


@app.route("/draft/<draft_id>/new_scars")
@login_required
def draft_new_scars(draft_id):
    d = DraftWrapper(draft_id, current_user)
    d.seat.unlock_scars()
    return redirect(url_for('draft', draft_id=draft_id))


@app.route("/draft/<draft_id>/pick/<card_id>")
@login_required
def draft_pick(draft_id, card_id):
    dw = DraftWrapper(draft_id, current_user)
    dw.pick_card(card_id)
    return redirect("/draft/{}".format(draft_id))


@app.route("/draft/<draft_id>/results", methods=["POST"])
@login_required
def draft_result(draft_id):
    form = ResultForm()

    if form.validate_on_submit():
        # See if there is already a result for this matchup.
        result = MatchResult.query.filter(
            MatchResult.draft_id == draft_id,
            MatchResult.user_id == current_user.id,
            MatchResult.opponent_id == form.user_id.data,
        ).first()


        if not result:
            result = MatchResult()
            result.user_id=current_user.id
            result.opponent_id=form.user_id.data
            result.draft_id=draft_id

        result.wins=form.wins.data or 0
        result.losses=form.losses.data or 0
        result.draws=form.draws.data or 0

        db.session.add(result)
        db.session.add(result.get_or_create_inverse())
        db.session.commit()

    else:
        flash("Error submitting form")

    return redirect(url_for('draft', draft_id=draft_id))


@app.route("/draft/swap_sideboard/<card_id>")
@login_required
def draft_swap_sideboard(card_id):
    card = PackCard.query.get(card_id)
    card.sideboard = not card.sideboard
    db.session.add(card)
    db.session.commit()

    return redirect(url_for('draft', draft_id=card.draft_id))


@app.route("/draft/<draft_id>/undo/<user_id>")
@login_required
def draft_undo(draft_id, user_id):
    user = User.query.get(user_id)
    dw = DraftWrapper(draft_id, user)

    last_pick = PackCard.query \
        .filter(PackCard.picked_by_id == dw.seat.id) \
        .order_by(PackCard.picked_at.desc()) \
        .first()

    next_player_has_picked = last_pick.pack.num_picked > last_pick.pick_number + 1

    if not next_player_has_picked:
        last_pick.picked_by_id = None
        last_pick.pick_number = -1
        last_pick.picked_at = None
        db.session.add(last_pick)

        last_pick.draft.num_picked_tmp -=1
        db.session.add(draft)

        # Remove this card from the player's deck.
        deck = dw.draft.deck_for(user_id)
        deck.remove_by_id(last_pick.cube_card.id)
        db.session.add(deck)

        db.session.commit()

    else:
        flash("Next player has already picked. Can't undo.")

    return redirect(url_for('draft', draft_id=draft_id))


@app.route("/pack/<pack_id>/debug")
@login_required
def pack_debug(pack_id):
    return render_template('pack_debug.html', d=DraftDebugger.from_pack(pack_id))


@app.route('/draft/<draft_id>/cockatrice')
@login_required
def cockatrice_download(draft_id):
    cockatrice_folder = os.path.join(current_app.root_path, app.config['COCKATRICE_FOLDER'])
    filename = f"00-cockatrice-draft-{draft_id}.xml"
    combined = os.path.join(cockatrice_folder, filename)
    force_rebuild = request.args.get('force_rebuild')

    # Ensure folder for saving cockatrice files
    if not os.path.exists(cockatrice_folder):
        os.makedirs(cockatrice_folder)

    # Create the file if it doesn't already exist
    if not os.path.exists(combined) or force_rebuild:
        draft = Draft.query.get(draft_id)
        with open(combined, 'w') as fout:
            fout.write(cockatrice.export_to_cockatrice(draft.cube))

    return send_from_directory(
        directory=cockatrice_folder,
        filename=filename,
        as_attachment=True,
        cache_timeout=0 if force_rebuild else None,
    )
