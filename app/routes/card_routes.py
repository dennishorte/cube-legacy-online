import copy
import time
from datetime import datetime
from random import random

from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required

from app import app
from app.forms import *
from app.models.cube_models import *
from app.models.draft_models import *
from app.models.game_models import *
from app.models.user_models import *
from app.util import card_util
from app.util.cube_wrapper import CubeWrapper
from app.util.string import normalize_newlines


@app.route("/make_pack", methods=["POST"])
@login_required
def make_pack():
    form = PackMakerForm.factory()

    if form.validate_on_submit():
        cube = Cube.query.filter(Cube.name == form.cube_name.data).first()
        count = int(form.count.data)

        return redirect(url_for(
            'pack_of_cards',
            cube_id=cube.id,
            num_cards=count,
            random_seed=int(time.time())
        ))

    else:
        return 'Error making pack'


@app.route("/pack_of_cards/<cube_id>/<num_cards>/<random_seed>")
@login_required
def pack_of_cards(cube_id, num_cards, random_seed):
    num_cards = int(num_cards)

    randomizer = random.Random(random_seed)
    cube = Cube.query.get(cube_id)
    cube_wrapper = CubeWrapper(cube)

    cards = cube_wrapper.cards()
    randomizer.shuffle(cards)
    cards = cards[:num_cards]

    card_data = {}
    if cube.style_a == 'legacy':
        for card in cards:
            card_data[card.id] = card.get_json()

    return render_template(
        'pack_of_cards.html',
        title=f"Pack of {num_cards} cards from {cube.name}",
        cards=cards,
        card_data=card_data,
    )


@app.route("/cards_by_id", methods=["POST"])
@login_required
def cards_by_id():
    card_id = request.json.get('id')
    result = card_util.cards_by_id([card_id])
    return {
        'cards': { x.id: _make_card_data(x) for x in result['cards'] },
        'missing': result['missing'],
    }


@app.route("/cards_by_name", methods=["POST"])
@login_required
def cards_by_name():


    card_name = request.json.get('name')
    result = card_util.cards_by_name([card_name])

    multi = []
    for m in result['multiples']:
        multi.append([_make_card_data(x) for x in m])

    cards = {}
    for card in result['cards']:
        cards[card.id] = _make_card_data(card)

    return {
        'cards': { x.id: x.get_json() for x in result['cards'] },
        'missing': result['missing'],
        'multiples': multi,
    }


def _make_card_data(card):
    card_data = card.get_json()
    card_data['meta'] = {}
    card_data['meta']['cube_id'] = card.cube.id
    card_data['meta']['cube_name'] = card.cube.name
    card_data['meta']['cube_card_id'] = card.id
    card_data['meta']['card_editor_link'] = url_for('card_editor', card_id=card.id)
    return card_data


@app.route("/card/<card_id>/copy", methods=["POST"])
@login_required
def card_copy(card_id):
    form = CopyCardForm.factory()

    if form.validate_on_submit():
        card = CubeCard.query.get(card_id)
        new_card = card.copy_to(int(form.cube_id.data))

        return redirect(url_for('card_editor', card_id=new_card.id))

    else:
        return "Error copying card"


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

    card_json = card_util.empty_card_json()
    _card_update_copy_form_data_into_card_json(card_json, form)
    card.set_json(card_json)
    card.name_tmp = card_json['name']
    card.comment = form.comment.data.strip()

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
        card_data=None,
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

    from app.util.cube_data import CubeData
    from app.util.cube_data import CardPickInfo
    cube_data = CubeData(card.cube)
    card_data = cube_data.info.get(card.latest_id, CardPickInfo(card))

    return render_template(
        'card_editor.html',
        title="Card Editor",
        mode='edit',
        card=card,
        scar=scar,
        read_only=read_only,
        card_data=card_data,

        form=form,
        alform=alform,
        rcform=RemoveCardForm(),
        copyform=CopyCardForm.factory(),
    )


@app.route("/card/<card_id>/flatten")
@login_required
def card_flatten(card_id):
    card = CubeCard.query.get(card_id)
    card.is_original = True
    card.version = 1
    db.session.add(card)

    all_versions = CubeCard.query.filter(CubeCard.latest_id == card.latest_id).all()
    for dead in all_versions:
        if dead.id == card.id:
            continue

        db.session.delete(dead)

    db.session.commit()

    return redirect(url_for('card_editor', card_id=card_id))


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
    card_json = copy.deepcopy(card.get_json())
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
