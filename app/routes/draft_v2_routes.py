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
from app.util.draft_wrapper import DraftWrapper


@app.route("/draft_v2/<draft_id>")
@login_required
def draft_v2(draft_id):
    draft = DraftV2.query.get(draft_id)

    return render_template(
        'draft_v2.html',
        draft = draft,
    )


@app.route('/draft_v2/<draft_id>/add_user/<user_id>')
@login_required
def draft_v2_add_user(draft_id, user_id):
    pass


@app.route('/draft_v2/new')
@login_required
def draft_v2_new():
    draft = DraftV2()
    db.session.add(draft)
    db.session.commit()

    draft.name = f"New Draft {draft.id}"
    db.session.add(draft)
    db.session.commit()

    draft_info = DraftInfo({})
    draft_info.name_set(draft.name)
    draft.info_set(draft_info)

    draft.user_add(current_user)
    draft.info_save()

    return redirect(url_for('draft_v2', draft_id=draft.id))



    # if draft_style == "cube":
    #     form = NewCubeDraftForm.factory()

    #     if form.validate_on_submit():
    #         from app.util.draft.draft_creator import create_pack_draft
    #         draft = create_pack_draft(
    #             name=form.name.data,
    #             cube_name=form.cube.data,
    #             pack_size=form.packsize.data,
    #             num_packs=form.numpacks.data,
    #             user_names=form.players.data,
    #             scar_rounds=form.scar_rounds.data,
    #             parent_id=form.parent.data,
    #         )
    #         return redirect(url_for('draft_v2', draft_id=draft.id))

    #     else:
    #         return "Unable to create new draft"

    # elif draft_style == "rotisserie":
    #     form = NewRotisserieDraftFrom.factory()

    #     if form.validate_on_submit():
    #         from app.util.draft.draft_creator import create_rotisserie_draft

    #         draft = create_rotisserie_draft(
    #             name = form.name.data.strip(),
    #             cube = Cube.query.get(form.cube_id).first(),
    #         )
    #         return redirect(url_for('draft_v2', draft_id=draft.id))

    #     else:
    #         return "Unable to create new draft"

    # else:
    #     return f"Unknown draft type: {draft_style}"


@app.route('/draft_v2/<draft_id>/start')
@login_required
def draft_v2_start(draft_id):
    pass
