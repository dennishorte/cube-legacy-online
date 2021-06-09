from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import login_required
from flask_login import logout_user

from app import app
from app import db
from app.forms import *
from app.models.cube_models import *
from app.models.deck_models import *
from app.models.draft_v2_models import *
from app.models.user_models import *
from app.util.draft.draft_info import DraftInfo
from app.util.draft.round_builder import RoundBuilder
from app.util.draft_wrapper import DraftWrapper


@app.route("/draft_v2/<draft_id>")
@login_required
def draft_v2(draft_id):
    draft = DraftV2.query.get(draft_id)
    all_users = User.query.order_by(User.name).all()
    all_cubes = Cube.query.order_by(Cube.name).all()

    user_map = {}
    for user_id in draft.info().user_ids():
        user_map[user_id] = User.query.get(user_id)

    return render_template(
        'draft_v2.html',
        draft = draft,
        all_cubes = all_cubes,
        all_users = all_users,  # Used for adding new users
        user_map = user_map,  # Used for fetching user data from game data
    )


@app.route('/draft_v2/<draft_id>/deck_save', methods=["POST"])
@login_required
def draft_v2_deck_save(draft_id):
    draft = DraftV2.query.get(draft_id)
    draft.info().deck_update(current_user, request.json)
    draft.info_save()
    return 'success'


@app.route('/draft_v2/<draft_id>/force/<user_id>')
@login_required
def draft_v2_force(draft_id, user_id):
    return "force"


@app.route('/draft_v2/<draft_id>/name_update')
@login_required
def draft_v2_name_update(draft_id):
    new_name = request.args.get('name').strip()
    if not new_name:
        return "Empty name specified"

    draft = DraftV2.query.get(draft_id)
    draft.name_set(new_name)

    return redirect(url_for('draft_v2', draft_id=draft_id))


@app.route('/draft_v2/new')
@login_required
def draft_v2_new():
    draft = DraftV2()
    db.session.add(draft)
    db.session.commit()

    draft.name = f"New Draft {draft.id}"
    db.session.add(draft)
    db.session.commit()

    draft_info = DraftInfo.factory(draft.id)
    draft_info.name_set(draft.name)
    draft.info_set(draft_info)

    draft.user_add(current_user)
    draft.info_save()

    return redirect(url_for('draft_v2', draft_id=draft.id))


@app.route('/draft_v2/<draft_id>/pack_pick/<card_id>')
@login_required
def draft_v2_pack_pick(draft_id, card_id):
    draft = DraftV2.query.get(draft_id)
    draft.info().make_pack_pick(current_user, card_id)
    draft.check_if_complete()
    draft.info_save()

    return redirect(url_for('draft_v2', draft_id=draft_id))


@app.route('/draft_v2/<draft_id>/round_add')
@login_required
def draft_v2_round_add(draft_id):
    draft = DraftV2.query.get(draft_id)

    cube_id = int(request.args.get('cube_id'))
    cube = Cube.query.get(cube_id)
    style = request.args.get('style')

    if style == 'cube-pack':
        draft.info().round_add({
            'style': style,
            'cube_id': cube_id,
            'cube_name': cube.name,
            'pack_size': int(request.args.get('pack_size')),
            'num_packs': int(request.args.get('num_packs')),
            'scar_rounds': [int(x) for x in request.args.get('scar_rounds').split(',') if x.strip()],
        })

    elif style == 'rotisserie':
        draft.info().round_add({
            'style': style,
            'cube_id': cube_id,
            'num_cards': int(request.args.get('num_cards')),
        })

    else:
        raise ValueError(f"Unknown round style: {style}")

    draft.info_save()

    return redirect(url_for('draft_v2', draft_id=draft_id))


@app.route('/draft_v2/<draft_id>/start')
@login_required
def draft_v2_start(draft_id):
    draft = DraftV2.query.get(draft_id)
    assert draft.state == DraftStates.SETUP, f"Can't start a draft in state {draft.state}"

    info = draft.info()

    for round_setup in info.rounds():
        new_card_data = RoundBuilder.build(round_setup, draft.info().user_data())
        info.card_data().update(new_card_data)

    info.round_start(info.rounds()[0])

    draft.state = DraftStates.ACTIVE
    draft.info_save()

    return redirect(url_for('draft_v2', draft_id=draft_id))


@app.route('/draft_v2/<draft_id>/user_add')
@login_required
def draft_v2_user_add(draft_id):
    draft = DraftV2.query.get(draft_id)

    ids = request.args.get('ids').split(',')
    for user in User.query.filter(User.id.in_(ids)).all():
        draft.user_add(user)

    draft.info_save()

    return redirect(url_for('draft_v2', draft_id=draft_id))
