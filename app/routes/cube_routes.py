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
from app.forms import LinkAchievemetAndCardForm
from app.forms import NewAchievementForm
from app.forms import NewCubeForm
from app.forms import NewFactionForm
from app.forms import NewScarForm
from app.forms import RandomScarsForm
from app.forms import UseScarForm
from app.models.cube import *
from app.models.draft import *
from app.models.user import *
from app.util.card_table import CardTable
from app.util.cube_data import CubeData
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
        for fieldName, errorMessages in form.errors.items():
            print('+++++' + fieldName)
            for err in errorMessages:
                print('...'+err)

        return 'failed'


@app.route("/cubes/<cube_id>/cards")
@login_required
def cube_cards(cube_id):
    add_cards_form = AddCardsForm()
    cube = Cube.query.get(cube_id)
    return render_template(
        'cube_cards.html',
        cube=cube,
        t=CardTable(cube),
        add_cards_form=add_cards_form,
    )


@app.route("/cubes/<cube_id>/data")
@login_required
def cube_data(cube_id):
    cube = Cube.query.get(cube_id)
    data = CubeData(cube)

    return render_template(
        'cube_data.html',
        cube=cube,
        d=data,
    )


@app.route("/cube/<cube_id>/factions")
@login_required
def cube_factions(cube_id):
    cube = Cube.query.get(cube_id)
    form = NewFactionForm()

    achievements = [x for x in cube.achievements_avaiable() if 'faction' in x.conditions.lower()]

    return render_template(
        'cube_factions.html',
        cube=cube,
        form=form,
        achievements=achievements,
    )


@app.route("/cube/<cube_id>/interns")
@login_required
def cube_interns(cube_id):
    cube = Cube.query.get(cube_id)

    card = CubeCard.query.filter(
        CubeCard.cube_id == cube.id,
        CubeCard.latest_id == CubeCard.id,
    )
    interns = [x for x in card if 'intern of' in x.oracle_text().lower()]

    live_interns = [x for x in interns if not x.removed_by_id]
    dead_interns = [x for x in interns if x.removed_by_id]

    live_interns.sort(key=lambda x: x.timestamp, reverse=True)
    dead_interns.sort(key=lambda x: x.removed_by_timestamp, reverse=True)

    return render_template(
        'cube_interns.html',
        cube=cube,
        live_interns=live_interns,
        dead_interns=dead_interns,
    )


@app.route("/cube/<cube_id>/factions/edit", methods=["POST"])
@login_required
def cube_edit_faction(cube_id):
    cube = Cube.query.get(cube_id)
    form = NewFactionForm()

    if form.validate_on_submit():
        if form.id.data:
            faction = Faction.query.get(form.id.data)
            flash('Faction updated')
        else:
            faction = Faction()
            faction.cube_id = cube_id
            flash('New faction created!')

        faction.name = form.name.data.strip()
        faction.desc = form.desc.data.strip()
        faction.memb = form.memb.data.strip()
        faction.note = form.note.data.strip()

        db.session.add(faction)
        db.session.commit()


    else:
        flash('Error creating new faction')

    return redirect(url_for('cube_factions', cube_id=cube_id))


@app.route("/cube/<cube_id>/link_achievement", methods=["POST"])
@login_required
def cube_link_achievement(cube_id):
    form = LinkAchievemetAndCardForm.factory(cube_id)

    card = CubeCard.query.get(form.card.data)
    ach = Achievement.query.get(form.achievement.data)
    assert card.cube_id == ach.cube_id

    existing_link = AchievementLink.query.filter(
        AchievementLink.card_id == card.id,
        AchievementLink.ach_id == ach.id,
    ).first()

    if existing_link:
        flash(f"Link already exists for {card.name()} to {ach.name}")

    else:
        link = AchievementLink(
            card_id=card.id,
            ach_id=ach.id,
        )
        db.session.add(link)
        db.session.commit()
        flash(f"Linked {card.name()} to {ach.name}")

    return redirect(request.referrer)


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
