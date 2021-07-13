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
            user.slack_id = form.slack_id.data.strip()

            db.session.add(user)
            db.session.commit()

            flash("New user created")

        else:
            return "empty username or password <= 10 characters"

    else:
        return "form error"

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


@app.route("/admin/cogwork_librarian_update")
@login_required
def admin_cogwork_librarian_update():
    if not current_user.is_admin:
        return "Not allowed"

    for draft in DraftV2.query.all():
        info = draft.info()

        if 'messages' not in info.data:
            info.data['messages'] = []

        for rnd in info.rounds():
            if 'packs' in rnd:
                for pack in rnd['packs']:
                    pack['waiting_picks'] = 1

        for user_id in info.user_ids():
            user_data = info.user_data(user_id)

            if 'cogwork_librarian_ids' not in user_data:
                user_data['cogwork_librarian_ids'] = []

                deck = info.deck_info(user_id)
                for card_id in deck.card_ids():
                    card = deck.card_wrapper(card_id)
                    if 'cogwork librarian' in card.name().lower():
                        user_data['cogwork_librarian_ids'].append(card_id)

        draft.info_save()

    return redirect(url_for('admin'))


@app.route("/admin/deck_fix")
@login_required
def admin_deck_fix():
    for draft in DraftV2.query.all():
        info = draft.info()
        for user_id in info.user_ids():
            deck = info.deck_info(user_id)
            deck.clean_ids()

        draft.info_save()

    return redirect(url_for('admin'))


@app.route("/admin/game_user_link")
@login_required
def admin_game_user_link():
    if not current_user.is_admin:
        return "Not allowed"

    for game in Game.query.all():
        for player in game.state.players:
            user = User.query.get(player.id)
            existing = GameUserLink.query.filter(
                GameUserLink.game_id == game.id,
                GameUserLink.user_id == user.id,
            ).all()

            if not existing:
                link = GameUserLink(game_id=game.id, user_id=user.id)
                db.session.add(link)

    db.session.commit()

    return redirect(url_for('admin'))


@app.route("/admin/name_fix")
@login_required
def admin_name_fix():
    if not current_user.is_admin:
        return "Not allowed"

    for card in CubeCard.query.all():
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
