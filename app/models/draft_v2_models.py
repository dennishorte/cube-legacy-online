import json
from datetime import datetime

from sqlalchemy.dialects.mysql import MEDIUMTEXT

from app import db
from app.models.cube_models import *
from app.models.deck_models import *
from app.models.user_models import *


class DraftV2(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    name = db.Column(db.String(64))

    # 'active', 'complete', 'killed'
    state = db.Column(db.String(32))

    data_json = db.Column(MEDIUMTEXT)

    def wrapper(self):
        data = json.loads(self.data_json)
        return DraftInfoBase.from_data(data)


class DraftAchievementLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey("draft_v2.id"), nullable=False)
    ach_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)


class DraftUserLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey("draft_v2.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
