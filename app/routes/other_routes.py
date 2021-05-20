from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from flask_login import logout_user

from app import app
from app.forms import *
from app.models.cube_models import *
from app.models.draft_models import *
from app.models.game_models import *
from app.models.user_models import *


@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    complete_seats = [x for x in current_user.draft_seats if x.draft.complete]
    complete_seats.sort(key=lambda x: x.draft.timestamp, reverse=True)

    achievements_unfinished = [x for x in current_user.achievements_unlocked if not x.finalized_timestamp]
    achievements_unfinished.sort(key=lambda x: x.unlocked_timestamp, reverse=True)


    achievements_finished = [x for x in current_user.achievements_unlocked if x.finalized_timestamp]
    achievements_finished.sort(key=lambda x: x.unlocked_timestamp, reverse=True)

    cubes = Cube.query.filter(
        Cube.admin != True,
        Cube.active == True,
    ).all()
    users = User.query.filter(User.name != 'starter').order_by(User.name).all()

    return render_template(
        'index.html',
        active = current_user.active_draft_seats(),
        complete = complete_seats,
        achievements_unfinished = achievements_unfinished,
        achievements_finished = achievements_finished,

        new_cube_draft_form = NewCubeDraftForm.factory(),
        new_rotisserie_draft_form = NewRotisserieDraftForm.factory(),
        new_cube_form = NewCubeForm(),
        new_set_form = NewSetForm(),
        pack_maker_form = PackMakerForm.factory(15),

        cubes = cubes,
        games = current_user.all_games(),
        users = users,
    )


@app.route("/my_account")
@login_required
def my_account():
    return render_template(
        'my_account.html',
        user=current_user,
        pwform=ChangePasswordForm(),
        udform=ChangeUserDetailsForm(),
    )


@app.route("/my_account/change_details", methods=["POST"])
@login_required
def my_account_change_details():
    form = ChangeUserDetailsForm()

    if form.validate_on_submit():
        if form.slack_id.data.strip():
            current_user.slack_id = form.slack_id.data.strip()
            db.session.add(current_user)
            db.session.commit()

    else:
        flash("Error in user details form")

    return redirect(url_for('my_account'))


@app.route("/my_account/change_password", methods=["POST"])
@login_required
def my_account_change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        old_password = form.old_password.data.strip()
        new_password = form.new_password.data.strip()

        if current_user.check_password(old_password):
            if new_password:
                current_user.set_password(new_password)
                db.session.add(current_user)
                db.session.commit()
                flash("Please login with your new password")
                logout_user()

            else:
                flash("Invalid new password")

        else:
            flash("Old password is incorrect")

    else:
        flash("Error in password change form")

    return redirect(url_for('my_account'))


@app.route("/levelup/manage")
@login_required
def levelup_manage():
    return render_template(
        "levelup_manager.html",
        levelups=Levelup.query.order_by(Levelup.xp).all(),
    )


@app.route("/levelup/update", methods=["POST"])
@login_required
def levelup_update():
    data = request.json

    if data['id'] == 'new':
        levelup = Levelup()
    else:
        levelup = Levelup.query.get(data['id'])

    levelup.xp = data['xp']
    levelup.reward = '\n'.join([x.strip() for x in data['reward'].split('\n')])
    db.session.add(levelup)
    db.session.commit()

    return 'saved'
