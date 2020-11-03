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
from app.util.draft_debugger import DraftDebugger
from app.util.draft_wrapper import DraftWrapper
from app.util.string import normalize_newlines


@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    active_seats = [x for x in current_user.draft_seats if not x.draft.complete and not x.draft.killed]
    active_seats.sort(key=lambda x: x.draft.timestamp, reverse=True)
    
    complete_seats = [x for x in current_user.draft_seats if x.draft.complete]
    complete_seats.sort(key=lambda x: x.draft.timestamp, reverse=True)

    achievements_unfinished = [x for x in current_user.achievements_unlocked if not x.finalized_timestamp]
    achievements_unfinished.sort(key=lambda x: x.unlocked_timestamp, reverse=True)

    
    achievements_finished = [x for x in current_user.achievements_unlocked if x.finalized_timestamp]
    achievements_finished.sort(key=lambda x: x.unlocked_timestamp, reverse=True)

    cubes = Cube.query.all()

    return render_template(
        'index.html',
        active=active_seats,
        complete=complete_seats,
        achievements_unfinished=achievements_unfinished,
        achievements_finished=achievements_finished,
        new_draft_form=_new_draft_form(),
        new_cube_form=NewCubeForm(),
        pack_maker_form=PackMakerForm.factory(15),
        cubes=cubes,
    )


@app.route("/make_pack", methods=["POST"])
@login_required
def make_pack():
    form = PackMakerForm.factory()

    # Get form data
    cube = Cube.query.filter(Cube.name == form.cube_name.data).first()
    count = int(form.count.data)

    # Make pack
    if form.obj_type.data == 'Cards':
        cards = cube.cards()
        random.shuffle(cards)
        cards = cards[:count]

    elif form.obj_type.data == 'Dead Interns':
        removed_cards = cube.cards_removed()
        interns = [x for x in removed_cards if 'intern of ' in x.get_json()['oracle_text'].lower()]
        cards = interns[:count]

    if form.validate_on_submit():
        return render_template(
            'pack_of_cards.html',
            title=f"Pack of {count} cards from {cube.name}",
            cards=cards,
        )

    else:
        return 'Error making pack'


@app.route("/cube/<cube_id>/create", methods=["POST"])
@login_required
def card_create(cube_id):
    form = EditMultiFaceCardForm()
    form.update_as.choices = User.all_names()
    form.group_fields()

    if not form.validate_on_submit():
        flash('Error Creating Card')
        return redirect(url_for('card_creator', cube_id=cube_id))

    if form.face_0_name.data == '':
        flash('Card front face must have a name')
        return redirect(url_for('card_creator', cube_id=cube_id))

    card = CubeCard()
    card.added_by_id = User.query.filter(User.name == form.update_as.data).first().id
    card.cube_id = cube_id
    card.is_original = True
    card.version = 1

    card_json = empty_card_json()
    _card_update_copy_form_data_into_card_json(card_json, form)
    card.set_json(card_json)

    db.session.add(card)
    db.session.commit()

    card.latest_id = card.id
    db.session.add(card)
    db.session.commit()
    
    flash('Card Created')
    return redirect(url_for('card_editor', card_id=card.id))


@app.route("/cube/<cube_id>/creator")
@login_required
def card_creator(cube_id):
    form = EditMultiFaceCardForm()
    form.group_fields()
    form.comment.data = f"Created by: {current_user.name}"
    form.update_as.choices = User.all_names()
    form.update_as.data = current_user.name

    return render_template(
        'card_editor.html',
        title='Card Creator',
        mode='create',
        cube=Cube.query.get(cube_id),
        card=None,
        form=form,
        scar=None,
        read_only=False,
    )


@app.route("/card/<card_id>")
@login_required
def card_editor(card_id):
    """
    Possible URL params
    - scar_id: Loads the editor with information about the scar to help in applying it.
    - read_only: Disables all of the form fields to prevent changes to the card.
    """
    card = CubeCard.query.get(card_id)
    form = EditMultiFaceCardForm()
    form.group_fields()

    # Copy card face data into form
    card_faces = card.card_faces()
    for face_index in range(len(card_faces)):
        form_fields = form.faces[face_index]
        for field_name, field in form_fields.items():
            field.data = card_faces[face_index].get(field_name, '')
    
    # Generic Pieces
    form.layout.data = card.get_json().get('layout', '')
    form.update_as.choices = User.all_names()
    form.update_as.data = current_user.name

    # Achievement link form
    alform = LinkAchievemetAndCardForm.factory(
        cube_id=card.cube_id,
        card=card
    )

    # Adding a specific scar?
    scar_id = request.args.get('scar_id')
    scar = Scar.query.get(scar_id)
    if scar:
        form.comment.data = "{} added scar during draft: {}".format(current_user.name, scar.text)
        form.scar_id.data = scar_id

    if card.removed_by_timestamp:
        read_only = 'true'
    else:
        read_only = request.args.get('read_only', ''),

    return render_template(
        'card_editor.html',
        title="Card Editor",
        mode='edit',
        card=card,
        rcform=RemoveCardForm(),
        scar=scar,
        read_only=read_only,
        form=form,
        alform=alform,
    )


@app.route("/card/<card_id>/remove", methods=["POST"])
@login_required
def card_remove(card_id):
    form = RemoveCardForm()
    
    card = CubeCard.query.get(card_id)
    card.removed_by_id = current_user.id
    card.removed_by_comment = form.comment.data
    card.removed_by_timestamp = datetime.utcnow()

    db.session.add(card)
    db.session.commit()

    flash(f"Removed {card.name()} from cube.")
    return redirect(url_for('cube_cards', cube_id=card.cube_id))


@app.route("/card/<card_id>/update", methods=["POST"])
@login_required
def card_update(card_id):
    form = EditMultiFaceCardForm()
    form.update_as.choices = User.all_names()
    form.group_fields()

    if not form.validate_on_submit():
        flash('Error on Update')
        return redirect(url_for('card_editor', card_id=card_id))

    card = CubeCard.query.get(card_id)
    card_json = card.get_json().copy()
    _card_update_copy_form_data_into_card_json(card_json, form)

    if not form.comment.data:
        form.comment.data = "Edited by {}".format(current_user.name)

    editor = User.query.filter(User.name == form.update_as.data).first()

    # Create a new version of the card
    new_version_created = card.update(
        new_json=card_json,
        edited_by=editor,
        comment=form.comment.data,
        commit=False,
    )

    # Give the user some feedback on what happened.
    if new_version_created:
        return_to_draft_id = _apply_scar_from_editor(card, form.scar_id.data)
        db.session.commit()

        if return_to_draft_id:
            return redirect(url_for('draft', draft_id=return_to_draft_id))
        
        flash('Card Updated')
    else:
        flash('No changes detected')

    return redirect(url_for('card_editor', card_id=card_id))


def _apply_scar_from_editor(card, scar_id):
    if not scar_id:
        return None

    scar = Scar.query.get(scar_id)
    scar.applied_timestamp = datetime.utcnow()
    scar.applied_by_id = current_user.id
    scar.applied_to_id = card.id
    db.session.add(scar)

    # Unlock the scars if they're from a draft.
    # The most common case is that the scar was applied from a draft.
    pack = Pack.query.get(scar.locked_pack_id)
    if pack and scar.locked_by_id == current_user.id:
        pack.scarred_this_round_id = card.id
        db.session.add(pack)
        for pack_scar in Scar.get_for_pack(pack.id, current_user.id):
            pack_scar.unlock(commit=False)
            db.session.add(pack_scar)
        return pack.draft_id

    else:
        return None


def _card_update_copy_form_data_into_card_json(card_json, form):
    card_faces = card_json['card_faces']
    while len(card_faces) < len(form.faces):
        card_faces.append({})

    # Copy the data from the form into the card_faces dicts.
    for face_index in range(len(form.faces)):
        card_face = card_faces[face_index]
        for field_name, field in form.faces[face_index].items():
            card_face[field_name] = normalize_newlines(field.data.strip())

    # Remove any dicts face dicts that don't have names.
    # This happens often for normal layout cards since there is always a second face form.
    card_faces = [x for x in card_faces if x.get('name', False)]
    card_json['card_faces'] = card_faces

    # Update the root fields
    card_json['layout'] = form.layout.data.strip()
    card_json['name'] = ' // '.join([x['name'] for x in card_faces])
    card_json['type_line'] = ' // '.join([x['type_line'] for x in card_faces])
    card_json['oracle_text'] = '\n-----\n'.join([x['oracle_text'] for x in card_faces])

    
@app.route("/card/<card_id>/json", methods=['POST'])
@login_required
def card_json(card_id):
    card = CubeCard.query.get(card_id)
    if not card:
        return 'Unknown Card'
    else:
        return card.get_json()


@app.route('/draft/new', methods=['POST'])
@login_required
def new_draft():
    form = _new_draft_form()

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


def _new_draft_form():
    new_draft_form = NewDraftForm()

    cube_names = [x.name for x in Cube.query.order_by('name')]
    new_draft_form.cube.choices = cube_names

    user_names = [(x.name, x.name) for x in User.query.order_by('name') if x.name != 'starter']
    new_draft_form.players.choices = user_names

    return new_draft_form
    

@app.route("/draft/<draft_id>")
@login_required
def draft(draft_id):
    dw = DraftWrapper(draft_id, current_user)
    return render_template('draft.html', d=dw)


@app.route("/draft/<draft_id>/kill")
@login_required
def draft_kill(draft_id):
    draft = Draft.query.get(draft_id)
    draft.killed = True
    db.session.add(draft)
    db.session.commit()

    return redirect(url_for('index'))
    

@app.route("/draft/swap_sideboard/<card_id>")
@login_required
def draft_swap_sideboard(card_id):
    card = PackCard.query.get(card_id)
    card.sideboard = not card.sideboard
    db.session.add(card)
    db.session.commit()

    return redirect(url_for('draft', draft_id=card.draft_id))
    

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


@app.route("/draft/<draft_id>/pick/<card_id>")
@login_required
def draft_pick(draft_id, card_id):
    dw = DraftWrapper(draft_id, current_user)
    dw.pick_card(card_id)
    return redirect("/draft/{}".format(draft_id))


@app.route("/draft/<draft_id>/force/<user_id>")
@login_required
def force_pick(draft_id, user_id):
    user = User.query.get(user_id)
    dw = DraftWrapper(draft_id, user)

    # Pick the first card in the pack.
    if dw.pack:
        dw.seat.unlock_scars()
        dw.pick_card(dw.pack.unpicked_cards()[0].id)
        
    return redirect("/draft/{}".format(draft_id))


@app.route("/draft/<draft_id>/debug")
@login_required
def draft_debug(draft_id):
    draft_debugger = DraftDebugger(draft_id)
    return render_template('draft_debug.html', d=draft_debugger)


@app.route("/draft/<draft_id>/new_scars")
@login_required
def draft_new_scars(draft_id):
    d = DraftWrapper(draft_id, current_user)
    d.seat.unlock_scars()
    return redirect(url_for('draft', draft_id=draft_id))


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
