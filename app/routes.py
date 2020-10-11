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

    # Front face of card
    front_json = card.front_json()
    form.front_name.data = front_json['name']
    form.front_mana_cost.data = front_json['mana_cost']
    form.front_image_url.data = front_json['image_url']
    form.front_type_line.data = front_json['type_line']
    form.front_rules_text.data = front_json['oracle_text']
    form.front_power.data = front_json.get('power', '')
    form.front_toughness.data = front_json.get('toughness', '')
    form.front_loyalty.data = front_json.get('loyalty', '')

    # Back face of card
    back_json = card.back_json()
    if back_json:
        form.back_name.data = back_json['name']
        form.back_mana_cost.data = back_json['mana_cost']
        form.back_image_url.data = back_json['image_url']
        form.back_type_line.data = back_json['type_line']
        form.back_rules_text.data = back_json['oracle_text']
        form.back_power.data = back_json.get('power', '')
        form.back_toughness.data = back_json.get('toughness', '')
        form.back_loyalty.data = back_json.get('loyalty', '')
    
    # Generic Pieces
    form.layout.data = front_json['layout']

    return render_template('card_editor.html', card=card, form=form)


@app.route("/card/<card_id>/update", methods=["POST"])
@login_required
def card_update(card_id):
    card = CubeCard.query.get(card_id)
    form = EditMultiFaceCardForm()

    if form.validate_on_submit():
        
        
        flash('Card Updated')

    return redirect(url_for('card_editor', card_id=card_id))

    
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
    return render_template('draft.html', d=dw)


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
