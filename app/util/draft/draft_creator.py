from app.models.draft_v2_models import *
from app.util.draft.draft_info import *


def create_pack_draft(
        name: str,
        pack_size: int,
        num_packs: int,
        scar_rounds: str,
        pack_style: str,
        cube,
):
    draft_info = PackDraft.factory(
        name = name,
        cube = cube,
        pack_size = pack_size,
        num_packs = num_packs,
        scar_rounds = scar_rounds,
        pack_style = pack_style,
    )

    return create_draft(name, draft_info)


def create_rotisserie_draft(
        name: str,
        user_ids: list,
        cube,
):
    draft_info = RotisserieDraft.factory(
        name = name,
        cube = cube,
    )

    return create_draft(draft_info)


def create_draft(draft_info):
    draft = DraftV2(
        name = name,
        state = active,
        data_json = draft_info.json_string(),
    )
    db.session.add(draft)
    db.session.commit()

    for user_id in draft_info.user_ids():
        link = DraftUserLink(
            draft_id = draft.id,
            user_id = user_id,
        )
        db.session.add(link)

    db.session.commit()

    return draft
