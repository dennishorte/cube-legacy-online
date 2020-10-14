from datetime import datetime

from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import login_required
from flask_login import logout_user
from is_safe_url import is_safe_url

from app import app
from app.forms import *
from app.models.cube import *
from app.models.draft import *
from app.models.user import *
from app.util.cube_util import add_cards_to_cube
from app.util.draft_debugger import DraftDebugger
from app.util.draft_wrapper import DraftWrapper
from app.util.string import normalize_newlines


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        
        if not next_page or not is_safe_url(next_page, request.host):
            next_page = url_for('index')
            
        return redirect(next_page)        
    
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    active_seats = [x for x in current_user.draft_seats if not x.draft.complete]
    complete_seats = [x for x in current_user.draft_seats if x.draft.complete]
    return render_template(
        'index.html',
        active=active_seats,
        complete=complete_seats,
        new_draft_form=_new_draft_form(),
    )


@app.route("/cubes", methods=['GET', 'POST'])
@login_required
def cubes():
    form = NewCubeForm()

    if form.validate_on_submit():
        cube = Cube.query.filter(Cube.name==form.name.data).first()
        if cube is not None:
            flash('A Cube with the name "{}" already exists.'.format(cube.name))
            return redirect(url_for('cubes'))

        cube = Cube(
            name=form.name.data,
            style=form.style.data,
        )
        db.session.add(cube)
        db.session.commit()
    
    cubes = Cube.query.all()
    return render_template(
        'cubes.html',
        active=[x for x in cubes if x.active],
        inactive=[x for x in cubes if not x.active],
        form=form
    )


@app.route("/cubes/<cube_id>")
@login_required
def cube_cards(cube_id):
    add_cards_form = AddCardsForm()
    cube = Cube.query.get(cube_id)
    return render_template(
        'cube_cards.html',
        cube=cube,
        add_cards_form=add_cards_form,
    )


@app.route("/cubes/<cube_id>/achievements")
@login_required
def cube_achievements(cube_id):
    return 'cube achievements'


@app.route("/cubes/<cube_id>/scars")
@login_required
def cube_scars(cube_id):
    form = NewScarForm()
    cube = Cube.query.get(cube_id)
    return render_template('cube_scars.html', cube=cube, form=form)


@app.route("/cubes/<cube_id>/scars/add", methods=["POST"])
@login_required
def cube_scars_add(cube_id):
    form = NewScarForm()

    if form.validate_on_submit():
        scar = Scar(
            cube_id=cube_id,
            text=form.text.data.strip(),
            restrictions=form.restrictions.data.strip(),
            created_by=current_user,
        )
        db.session.add(scar)
        db.session.commit()
            
    
    return redirect(url_for('cube_scars', cube_id=cube_id))


@app.route("/card/<card_id>")
@login_required
def card_editor(card_id):
    card = CubeCard.query.get(card_id)
    form = EditMultiFaceCardForm()

    card_faces = card.card_faces()

    for form_field in form:
        tokens = form_field.name.split('_', 2)
        if tokens[0] != 'face':
            continue

        face = int(tokens[1])
        field_name = tokens[2]

        if face < len(card_faces):
            form_field.data = card_faces[face].get(field_name, '')
        
    # Generic Pieces
    form.layout.data = card.get_json().get('layout', '')
    form.update_as.choices = [x.name for x in User.query.order_by(User.name)]
    form.update_as.data = current_user.name

    # Adding a specific scar?
    scar_id = request.args.get('scar_id')
    scar = Scar.query.get(scar_id)
    if scar:
        form.comment.data = "{} added scar during draft: {}".format(current_user.name, scar.text)
        form.scar_id.data = scar_id

    return render_template(
        'card_editor.html',
        card=card,
        form=form,
        scar=scar,
    )


@app.route("/card/<card_id>/update", methods=["POST"])
@login_required
def card_update(card_id):
    form = EditMultiFaceCardForm()
    form.update_as.choices = [x.name for x in User.query.order_by(User.name)]

    if not form.validate_on_submit():
        flash('Error on Update')
        return redirect(url_for('card_editor', card_id=card_id))

    card = CubeCard.query.get(card_id)
    card_json = card.get_json()
    _card_update_copy_form_data_into_card_json(card_json, form)

    if not form.comment.data:
        form.comment.data = "Edited by {}".format(current_user.name)

    editor = User.query.filter(User.name == form.update_as.data).first()

    # Create a new version of the card
    new_version_created = card.update(
        new_json=card_json,
        edited_by=editor,
        comment=form.comment.data,
    )

    # Mark the scar as used, if there was one.
    if form.scar_id.data and new_version_created:
        scar = Scar.query.get(form.scar_id.data)
        scar.applied_timestamp = datetime.utcnow()
        scar.applied_by_id = current_user.id
        scar.applied_to_id = card_id
        db.session.add(scar)
        db.session.commit()

    # Give the user some feedback on what happened.
    if new_version_created:
        flash('Card Updated')
    else:
        flash('No changes detected')

    return redirect(url_for('card_editor', card_id=card_id))


def _card_update_copy_form_data_into_card_json(card_json, form):
    card_faces = card_json['card_faces']

    # Copy the data from the form into the card_faces dicts.
    for form_field in form:
        tokens = form_field.name.split('_', 2)
        if tokens[0] != 'face':
            continue

        face = int(tokens[1])
        field_name = tokens[2]
        field_value = normalize_newlines(form_field.data.strip())

        while face >= len(card_faces):
            card_faces.append({})

        card_faces[face][field_name] = field_value

    # Remove any dicts face dicts that don't have names.
    # This happens often for normal layout cards since there is always a second face form.
    card_faces = [x for x in card_faces if x.get('name', False)]
    card_json['card_faces'] = card_faces

    # Update the root fields
    card_json['layout'] = form.layout.data.strip()
    card_json['name'] = ' // '.join([x['name'] for x in card_faces])
    card_json['type_line'] = ' // '.join([x['type_line'] for x in card_faces])
    card_json['oracle_text'] = '\n-----\n'.join([x['oracle_text'] for x in card_faces])

    
@app.route("/cubes/<cube_id>/add", methods=["POST"])
@login_required
def add_cards(cube_id):
    form = AddCardsForm()

    if form.validate_on_submit():
        card_names = [x.strip() for x in form.cardnames.data.split('\n') if x.strip()]

        if form.add_as_starter.data == True:
            added_by = User.query.filter(User.name == 'starter').first()
        else:
            added_by = current_user
        
        result = add_cards_to_cube(cube_id, card_names, added_by)

        flash('Added {} cards ({} unique)'.format(
            result['num_added'],
            result['num_unique_added'],
        ))
        
        for card_name in result['failed_to_fetch']:
            flash('Failed to fetch Scryfall data for: {}'.format(card_name))
            
        return 'success'

    else:
        return 'failed'


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

    if dw.draft.complete:
        return render_template('draft_complete.html', d=dw)
    else:
        return render_template('draft_picker.html', d=dw)


@app.route("/draft/<draft_id>/results", methods=["POST"])
@login_required
def draft_result(draft_id):
    form = ResultForm()

    if form.validate_on_submit():
        # See if there is already a result for this matchup.
        result = MatchResult.query.filter(
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
        dw.pick_card(dw.pack.unpicked_cards()[0].id)
    return redirect("/draft/{}".format(draft_id))

@app.route("/draft/<draft_id>/debug")
@login_required
def draft_debug(draft_id):
    draft_debugger = DraftDebugger(draft_id)
    return render_template('draft_debug.html', d=draft_debugger)
