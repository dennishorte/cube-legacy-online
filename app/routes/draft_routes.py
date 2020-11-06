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
from app.models.cube import *
from app.models.draft import *
from app.models.user import *
from app.util import cockatrice
from app.util.card_util import empty_card_json
from app.util.deck_builder import DeckBuilder
from app.util.draft_debugger import DraftDebugger
from app.util.draft_wrapper import DraftWrapper
from app.util.string import normalize_newlines


@app.route("/draft/<draft_id>")
@login_required
def draft(draft_id):
    dw = DraftWrapper(draft_id, current_user)
    return render_template('draft.html', d=dw)


@app.route("/draft/<draft_id>/debug")
@login_required
def draft_debug(draft_id):
    draft_debugger = DraftDebugger(draft_id)
    return render_template('draft_debug.html', d=draft_debugger)


@app.route("/draft/<draft_id>/deck_builder")
@login_required
def draft_deck_builder(draft_id):
    return render_template(
        'deck_builder.html',
        d=DeckBuilder(draft_id, current_user.id),
    )


@app.route("/draft/<draft_id>/deck_save", methods=["POST"])
@login_required
def draft_deck_save(draft_id):
    data = request.json

    maindeck = PackCard.query.filter(PackCard.id.in_(data['maindeck']))
    for card in maindeck:
        if card.sideboard:
            card.sideboard = False
            db.session.add(card)

    sideboard = PackCard.query.filter(PackCard.id.in_(data['sideboard']))
    for card in sideboard:
        if not card.sideboard:
            card.sideboard = True
            db.session.add(card)

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
        )
        return redirect('/')

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
    face_up = request.args.get('face_up', None)
    if face_up:
        face_up = DraftFaceUp[face_up]
    
    dw = DraftWrapper(draft_id, current_user)
    dw.pick_card(card_id, face_up)
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


@app.route("/draft/<draft_id>/save_decklist", methods=["POST"])
@login_required
def draft_save_decklist(draft_id):
    form = SaveDeckListForm()
    if form.validate_on_submit():
        decklist = DeckList(
            user_id=current_user.id,
            draft_id=draft_id,
            name=form.name.data.strip(),
            decklist=normalize_newlines(form.decklist.data.strip()),
        )
        db.session.add(decklist)
        db.session.commit()
    
    else:
        flash('Error saving decklist')

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
