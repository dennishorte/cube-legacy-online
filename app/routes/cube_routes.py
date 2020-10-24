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
from app.models.cube import *
from app.models.draft import *
from app.models.user import *
from app.util.cube_util import add_cards_to_cube


@app.route("/cubes/new", methods=['POST'])
@login_required
def cubes_new():
    form = NewCubeForm()

    if form.validate_on_submit():
        cube = Cube.query.filter(Cube.name==form.name.data).first()
        if cube is not None:
            flash('A Cube with the name "{}" already exists.'.format(cube.name))
            return redirect(url_for('index'))

        cube = Cube(
            name=form.name.data,
            style=form.style.data,
        )
        db.session.add(cube)
        db.session.commit()

    return redirect(url_for('index'))


@app.route("/cubes/<cube_id>/achievements")
@login_required
def cube_achievements(cube_id):
    form = NewAchievementForm()
    form.update_as.choices = User.all_names()
    form.update_as.data = current_user.name
    form.cube_id.data = cube_id
    form.group_fields()
        
    cube = Cube.query.get(cube_id)
    return render_template('cube_achievements.html', cube=cube, form=form)


@app.route("/cubes/<cube_id>/add", methods=["POST"])
@login_required
def cube_add_cards(cube_id):
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


@app.route("/cubes/<cube_id>/cards")
@login_required
def cube_cards(cube_id):
    add_cards_form = AddCardsForm()
    cube = Cube.query.get(cube_id)
    return render_template(
        'cube_cards.html',
        cube=cube,
        add_cards_form=add_cards_form,
    )


@app.route("/cubes/<cube_id>/scars", methods=["GET", "POST"])
@login_required
def cube_scars(cube_id):
    cube = Cube.query.get(cube_id)

    form = NewScarForm()
    form.update_as.choices = User.all_names()
    form.update_as.data = current_user.name

    rsform = RandomScarsForm()
    if rsform.validate_on_submit():
        random_scar_count = int(rsform.count.data)
        random_scars = Scar.random_scars(cube_id, random_scar_count)

    else:
        rsform.count.data = '2'
        random_scars = []

    use_scar_form = UseScarForm()
    use_scar_form.card_name.choices = [''] + [x.name() for x in cube.cards()]

    return render_template(
        'cube_scars.html',
        cube=cube,
        form=form,
        rsform=rsform,
        usform=use_scar_form,
        random_scars=random_scars,
    )


@app.route("/cubes/<cube_id>/scars/add", methods=["POST"])
@login_required
def cube_scars_add(cube_id):
    form = NewScarForm()
    form.update_as.choices = User.all_names()

    if not form.validate_on_submit():
        flash('Failed to create/update scar')
        return redirect(url_for('cube_scars', cube_id=cube_id))

    if form.update_id.data:
        scar = Scar.query.get(form.update_id.data)
    else:
        scar = Scar(cube_id=cube_id)
        
    if form.update_as.data:
        user = User.query.filter(User.name == form.update_as.data).first()
    else:
        user = current_user

    scar.text = form.text.data.strip()
    scar.restrictions = form.restrictions.data.strip()
    scar.created_by = user
    db.session.add(scar)
    db.session.commit()
    
    return redirect(url_for('cube_scars', cube_id=cube_id))


@app.route("/cubes/<cube_id>/use", methods=["POST"])
@login_required
def cube_scars_use(cube_id):
    cube = Cube.query.get(cube_id)
    
    form = UseScarForm()
    form.card_name.choices = [x.name() for x in cube.cards()]

    if not form.validate_on_submit():
        flash('Scar use failed')
        return redirect(url_for('cube_scars', cube_id=cube_id))        

    card = cube.get_card_by_name(form.card_name.data)
    scar = Scar.query.get(form.scar_id.data)

    if not card:
        flash(f'Invalid card name: {form.card_name.data}')
        return redirect(url_for('cube_scars', cube_id=cube_id))        

    if not scar:
        flash(f'Invalid scar id: {form.card_id.data}')
        return redirect(url_for('cube_scars', cube_id=cube_id))

    scar.applied_timestamp = datetime.utcnow()
    scar.applied_by_id = current_user.id
    scar.applied_to_id = card.id

    db.session.add(scar)
    db.session.commit()
            
    flash(f'Scar applied to {card.name()}')
    return redirect(url_for('cube_scars', cube_id=cube_id))
