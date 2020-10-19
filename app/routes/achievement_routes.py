from flask import redirect
from flask import render_template
from flask import url_for
from flask_login import current_user
from flask_login import login_required

from app import app
from app.forms import NewAchievementForm
from app.models.cube import *
from app.models.draft import *
from app.models.user import *


@app.route("/achievement/<achievement_id>/confirm_reveal")
@login_required
def achievement_confirm_reveal(achievement_id):
    achievement = Achievement.query.get(achievement_id)

    return render_template(
        'achievement_unlock_confirm.html',
        achievement=achievement,
    )


@app.route("/achievement/<achievement_id>/claim")
@login_required
def achievement_claim(achievement_id):
    achievement = Achievement.query.get(achievement_id)
    achievement.unlocked_by = current_user
    achievement.unlocked_timestamp = datetime.utcnow()
    db.session.add(achievement)
    db.session.commit()

    return redirect(url_for('achievement_reveal', achievement_id=achievement_id))


@app.route("/achievement/<achievement_id>/edit")
@login_required
def achievement_edit(achievement_id):
    ach = Achievement.query.get(achievement_id)
    form = NewAchievementForm()
    form.update_as.choices = User.all_names()
    form.update_id.data = ach.id
    form.group_fields()

    form.name.data = ach.name
    form.conditions.data = ach.conditions
    form.multiunlock.data = ach.multiunlock
    form.update_as.data = ach.created_by.name
    form.submit.label.text = 'Update'
    form.fill_from_json_list(ach.get_json())

    return render_template('achievement_edit.html', ach=ach, form=form)


@app.route("/achievement/<achievement_id>/finalize")
@login_required
def achievement_finalize(achievement_id):
    achievement = Achievement.query.get(achievement_id)
    achievement.finalized_timestamp = datetime.utcnow()
    db.session.add(achievement)
    db.session.commit()

    return redirect(url_for('index'))


@app.route("/achievement/<achievement_id>/reveal")
@login_required
def achievement_reveal(achievement_id):
    achievement = Achievement.query.get(achievement_id)

    return render_template(
        'achievement_unlock_reveal.html',
        achievement=achievement,
    )


@app.route("/achievement/submit", methods=["POST"])
@login_required
def achievement_submit():
    form = NewAchievementForm()
    form.update_as.choices = User.all_names()
    form.group_fields()
    
    if not form.validate_on_submit():
        flash('Error submitting achievement')
        if form.update_id.data:
            return redirect(url_for('achievement_edit', achievement_id=form.update_id.data))
        elif form.cube_id.data:
            return redirect(url_for('cube_achievements', cube_id=form.cube_id.data))
        else:
            return redirect(url_for('index'))

    if form.update_id.data:
        ach = Achievement.query.get(form.update_id.data)
    elif form.cube_id.data:
        ach = Achievement(cube_id=form.cube_id.data)
    else:
        raise ValueError("Can't create achievement with update_id or cube_id.")

    ach.name=form.name.data
    ach.conditions=form.conditions.data
    ach.set_json(form.unlock_json())
    ach.multiunlock=form.multiunlock.data
    ach.created_by=User.query.filter(User.name == form.update_as.data).first()

    db.session.add(ach)
    db.session.commit()        
        
    flash('Achievement Created')
    
    return redirect(url_for('cube_achievements', cube_id=ach.cube_id))
