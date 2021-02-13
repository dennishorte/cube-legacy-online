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


@app.route("/admin")
@login_required
def admin():
    if not current_user.is_admin:
        return "Not allowed"

    return render_template(
        'admin.html',
        cubes=Cube.query.filter(Cube.admin == True).all(),
        games=Game.active_games(),
        addform=AddUserForm(),
    )


@app.route("/admin/add_user", methods=["POST"])
@login_required
def admin_add_user():
    if not current_user.is_admin:
        return "Not allowed"

    form = AddUserForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        password = form.password.data.strip()

        if name and len(password) > 10:
            user = User()
            user.name = name
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash("New user created")

    return redirect(url_for('admin'))


@app.route("/admin/clear_diffs")
@login_required
def admin_clear_diffs():
    if not current_user.is_admin:
        return "Not allowed"

    for card in CubeCard.query.filter(CubeCard.diff != None).all():
        card.diff = None
        db.session.add(card)

    db.session.commit()

    return redirect(url_for('admin'))


@app.route("/admin/name_fix")
@login_required
def admin_name_fix():
    if not current_user.is_admin:
        return "Not allowed"

    for card in CubeCard.query.all():
        print(card.id)
        card_data = json.loads(card.json)
        if card_data:
            card.name_tmp = card_data.get('name', 'NO_NAME')
        else:
            card.name_tmp = 'NO_NAME'
        db.session.add(card)

    db.session.commit()

    return redirect(url_for('admin'))


@app.route("/admin/pick_info_update")
@login_required
def admin_pick_info_update():
    for card in CubeCard.query.filter(CubeCard.latest_id == CubeCard.id).all():
        card.pick_info_update(commit=False)

    db.session.commit()

    return redirect(url_for('admin'))
