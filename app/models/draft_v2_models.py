import json
from datetime import datetime

from sqlalchemy.dialects.mysql import MEDIUMTEXT

from app import db
from app.models.cube_models import *
from app.models.deck_models import *
from app.models.user_models import *
from app.util.draft.draft_info import DraftInfo


class DraftStates(object):
    SETUP = 'setup'
    ACTIVE = 'active'


class DraftV2(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    state = db.Column(db.String(32), default=DraftStates.SETUP)
    name = db.Column(db.String(64))
    data_json = db.Column(MEDIUMTEXT)

    def info(self, force_update=False):
        if not hasattr(self, '_info_cache') or force_update:
            self._info_cache = DraftInfo(json.loads(self.data_json))
        return self._info_cache

    def info_save(self):
        self.data_json = json.dumps(self._info_cache.data)
        db.session.add(self)
        db.session.commit()

    def info_set(self, info):
        assert isinstance(info, DraftInfo), "info must be of type DraftInfo"
        self._info_cache = info

    def name_set(self, name):
        self.name = name
        self.info().name_set(name)
        self.info_save()

    def user_add(self, user):
        if self.state != DraftStates.SETUP:
            raise RuntimeError(f"Can't add new users when state is {self.state}")

        if user.id in self.info().user_ids():
            return f"Duplicate user id: {user.id}"

        self.info().user_add(user)
        link = DraftUserLink(
            draft_id = self.id,
            user_id = user.id
        )
        db.session.add(link)


class DraftAchievementLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey("draft_v2.id"), nullable=False)
    ach_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)


class DraftUserLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey("draft_v2.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
