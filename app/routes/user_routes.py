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
from app.models.draft_v2_models import *
from app.models.game_models import *
from app.models.user_models import *


@app.route("/user/<user_id>")
@login_required
def user_profile(user_id):
    user = User.query.get(user_id)

    drafts = [x.draft() for x in user.draft_v2_links]

    return render_template(
        'user.html',
        user=user,
        drafts=drafts,

        pwform=ChangePasswordForm(),
        udform=ChangeUserDetailsForm(),

        moniker_form=EditMonikersForm.factory(user),
        portrait_form=EditPortraitForm(prefix='portrait'),
    )


@app.route("/user/<user_id>/all_games", methods=['POST'])
@login_required
def user_all_games(user_id):
    user = User.query.get(user_id)
    games_json = [{
        'name': game.state.name,
        'link': url_for('game', game_id=game.id),
        'result': game.state.result_for(int(user_id)),
    } for game in user.games_complete()]

    return { 'games': games_json }


@app.route("/user/<user_id>/set_monikers", methods=['POST'])
@login_required
def user_set_monikers(user_id):
    form = EditMonikersForm(prefix='monikers')

    if form.validate_on_submit():
        monikers = [x.strip() for x in form.monikers.data.split('\n') if x.strip()]
        user = User.query.get(user_id)
        user.set_monikers(monikers)

    return redirect(url_for('user_profile', user_id=user_id))


@app.route("/user/<user_id>/set_personas", methods=['POST'])
@login_required
def user_set_personas(user_id):
    form = EditPersonasForm()

    if form.validate_on_submit():
        personas = [x.strip() for x in form.personas.data.split('\n') if x.strip()]
        user = User.query.get(user_id)
        user.set_personas(personas)

    return redirect(url_for('user_profile', user_id=user_id))


@app.route("/user/<user_id>/levelup/story", methods=['POST'])
@login_required
def user_levelup_story(user_id):
    form = EditLevelupStoryForm(prefix='story')
    if form.validate_on_submit():
        levelup = Levelup.query.get(form.levelup_id.data)
        claim = levelup.claim_for(user_id)
        if not claim:
            claim = LevelupClaim(levelup_id = levelup.id, user_id = user_id)

        claim.story = '\n'.join([x.strip() for x in form.story.data.strip().split()])
        db.session.add(claim)
        db.session.commit()

    return redirect(url_for('user_profile', user_id=user_id))


@app.route("/user/<user_id>/set_portrait", methods=['POST'])
@login_required
def user_set_portrait(user_id):
    form = EditPortraitForm(prefix='portrait')

    if form.validate_on_submit():
        user = User.query.get(user_id)
        user.portrait_link = form.portrait.data.strip()
        db.session.add(user)
        db.session.commit()

    return redirect(url_for('user_profile', user_id=user_id))


@app.route("/user/<user_id>/update_stat", methods=['POST'])
@login_required
def user_update_stat(user_id):
    data = request.json

    if data['stat_name'] == 'xp':
        current_user.xp = int(data['stat_value'])
        db.session.add(current_user)
        db.session.commit()
        return 'success'

    else:
        return 'unknown stat'
