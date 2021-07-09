from flask import flash
from flask import redirect
from flask import render_template
from flask import url_for
from flask_login import current_user
from flask_login import login_required

from app import app
from app.forms import FinalizeAchievementForm
from app.forms import NewAchievementForm
from app.forms import SelectDraftForm
from app.models.cube_models import *
from app.models.draft_v2_models import *
from app.models.user_models import *


@app.route("/achievement/<achievement_id>/claim_confirmation")
@login_required
def achievement_claim_confirmation(achievement_id):
    """Step 1 in claiming an achievement"""
    achievement = Achievement.query.get(achievement_id)

    return render_template(
        'achievement_claim_confirmation.html',
        achievement=achievement,
    )


@app.route("/achievement/<achievement_id>/claim")
@login_required
def achievement_claim(achievement_id):
    """Step 2 in claiming an achievement"""
    achievement = Achievement.query.get(achievement_id)
    achievement.unlocked_by = current_user
    achievement.unlocked_timestamp = datetime.utcnow()
    db.session.add(achievement)
    db.session.commit()

    return redirect(url_for('achievement_view', achievement_id=achievement_id))


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
    form.xp_value.data = ach.xp or 1
    form.multiunlock.data = ach.multiunlock
    form.update_as.data = ach.created_by.name
    form.submit.label.text = 'Update'
    form.fill_from_json_list(ach.get_json())

    return render_template('achievement_edit.html', ach=ach, form=form)


@app.route("/achievement/<achievement_id>/finalize", methods=["POST"])
@login_required
def achievement_finalize(achievement_id):
    """Marks that a player has completed all of the steps in the achievements."""
    form = FinalizeAchievementForm()
    achievement = Achievement.query.get(achievement_id)

    should_clone = achievement.multiunlock and not achievement.finalized_timestamp

    if form.validate_on_submit():
        achievement.finalized_timestamp = datetime.utcnow()
        achievement.story = form.story.data
        db.session.add(achievement)
        db.session.commit()

        # Clone multi-unlocks
        if should_clone:
            new = achievement.clone()
            db.session.add(new)
            db.session.commit()

    else:
        print(form.errors)

    return redirect(url_for('achievement_view', achievement_id=achievement.id))


@app.route("/achievement/<achievement_id>/link_to_draft", methods=["POST"])
@login_required
def achievement_link_to_draft(achievement_id):
    form = SelectDraftForm.factory()

    if form.validate_on_submit():
        if int(form.draft.data) != 0:

            link = DraftV2AchievementLink.query.filter(
                DraftV2AchievementLink.ach_id == achievement_id,
            ).first()

            if not link:
                link = DraftV2AchievementLink()

            link.draft_id = form.draft.data
            link.ach_id = achievement_id
            db.session.add(link)
            db.session.commit()

    else:
        flash("Form validation failure")

    return redirect(url_for('achievement_view', achievement_id=achievement_id))


@app.route("/achievement/<ach_id>/star")
@login_required
def achievement_star(ach_id):
    star = AchievementStar.query.filter(
        AchievementStar.user_id == current_user.id,
        AchievementStar.ach_id == ach_id,
    ).first()

    if star:
        cube_id = star.achievement.cube_id
        db.session.delete(star)
        db.session.commit()

    else:
        star = AchievementStar(
            user_id=current_user.id,
            ach_id=ach_id,
        )
        db.session.add(star)
        db.session.commit()
        cube_id = star.achievement.cube_id

    return redirect(url_for('cube_achievements', cube_id=cube_id))


@app.route("/achievement/<achievement_id>/view")
@login_required
def achievement_view(achievement_id):
    """Step 3 in claiming an achievement"""
    achievement = Achievement.query.get(achievement_id)
    draft_form = SelectDraftForm.factory()
    form = FinalizeAchievementForm()
    link = DraftV2AchievementLink.query.filter(
        DraftV2AchievementLink.ach_id == achievement_id,
    ).first()

    return render_template(
        'achievement_view.html',
        achievement=achievement,
        form=form,
        dform=draft_form,
        link=link
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

    ach.name = form.name.data
    ach.conditions = form.conditions.data
    ach.xp = int(form.xp_value.data)
    ach.multiunlock = form.multiunlock.data
    ach.created_by = User.query.filter(User.name == form.update_as.data).first()
    ach.set_json(form.unlock_json())

    db.session.add(ach)
    db.session.commit()

    flash('Achievement Created')

    return redirect(url_for('cube_achievements', cube_id=ach.cube_id))
