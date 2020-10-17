import enum
import json
import random
from datetime import datetime

from app import db
from app.models.user import *
from app.util import cockatrice
from app.util.enum import Layout


class CubeStyle(enum.Enum):
    standard = 1
    legacy = 2


class BaseCard(db.Model):
    """Data fetched from Scryfall"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    json = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    cards = db.relationship('CubeCard', backref='base')

    def __repr__(self):
        return '<BaseCard {}>'.format(self.name)

    def get_json(self):
        return json.loads(self.json)
    
    def set_json(self, json_obj):
        self.json = json.dumps(json_obj)
    

class Cube(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    active = db.Column(db.Boolean, index=True, default=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    style = db.Column(db.Enum(CubeStyle))

    # Foreign Keys
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    _cards = db.relationship('CubeCard', backref='cube')
    achievements = db.relationship('Achievement', backref='cube')
    drafts = db.relationship('Draft', backref='cube')
    scars = db.relationship('Scar', backref='cube')

    def __repr__(self):
        return '<Cube {}>'.format(self.name)

    def achievements_avaiable(self):
        return [x for x in self.achievements if x.available()]

    def achievements_completed(self):
        return [x for x in self.achievements if not x.available()]

    def cards(self):
        """
        Get only the latest version of the cards in the cube.
        """
        return CubeCard.query.filter(
            CubeCard.cube_id == self.id,
            CubeCard.latest == True,
        ).all()


class CubeCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    version = db.Column(db.Integer)
    latest = db.Column(db.Boolean, default=True)
    json = db.Column(db.Text)
    comment = db.Column(db.Text)
    
    # Foreign Keys
    latest_id = db.Column(db.Integer)  # Used to keep a family together.
    cube_id = db.Column(db.Integer, db.ForeignKey('cube.id'))
    base_id = db.Column(db.Integer, db.ForeignKey('base_card.id'))
    added_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    edited_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    removed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    draft_cards = db.relationship('PackCard', backref='cube_card')
    scars = db.relationship('Scar', backref='applied_to')

    def __repr__(self):
        return '<CubeCard {}>'.format(self.get_json()['name'])

    def get_json(self):
        return json.loads(self.json)
    
    def set_json(self, json_obj):
        self.json = json.dumps(json_obj)

    def name(self):
        return self.get_json().get('name', 'NO_NAME')

    def image_urls(self):
        data = self.get_json()
        layout = data['layout']
        if Layout.simple_faced_layout(layout) or Layout.split_faced_layout(layout):
            return [data['card_faces'][0]['image_url']]
        elif Layout.double_sided_layout(layout):
            return [x['image_url'] for x in self.card_faces() if 'image_url' in x]
        else:
            raise ValueError(f"Unknown layout type: {layout}")

    def is_scarred(self):
        return self.version > 1

    def card_faces(self):
        return self.get_json()['card_faces']

    def cockatrice_name(self):
        data = self.get_json()
        return cockatrice._card_name(
            card_data=data,
            face_index=0,
            scarred=self.is_scarred(),
        )

    @classmethod
    def from_base_card(cls, cube_id, base_card, added_by):
        return CubeCard(
            version=1,
            cube_id=cube_id,
            base_id=base_card.id,
            json=base_card.json,
            added_by_id=added_by.id,
        )

    def update(self, new_json, edited_by, comment, commit=True):
        """
        Assuming any changes have been made in the JSON compared to this CubeCard,
        creates a copy of this cube card and adds it to the database as an old verison,
        and then updates this card with the new data. This preserves the card id for
        drafts, when cards will be edited during drafting.
        """
        if self.removed_by_id:
            raise ValueError("Can't edit a removed card.")

        if self.get_json() != new_json:
            # Create a copy of this card as a non-latest version.
            new_card = CubeCard(
                timestamp=self.timestamp,
                version=self.version,
                latest=False,
                json=self.json,

                cube_id=self.cube_id,
                base_id=self.base_id,
                added_by_id=self.added_by_id,
                edited_by_id=self.edited_by_id,
            )

            # Update this card with the new data.
            self.version += 1
            self.json = json.dumps(new_json)
            self.edited_by_id = edited_by.id
            self.comment = comment

            db.session.add(new_card)
            db.session.add(self)

            if commit:
                db.session.commit()

            return True  # Changes detected and card updated

        else:
            return False  # No change detected


class Scar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cube_id = db.Column(db.Integer, db.ForeignKey('cube.id'))

    # Content info
    text = db.Column(db.Text)
    restrictions = db.Column(db.String(128), default='')
    errata = db.Column(db.Text, default='')

    # Creation info
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Application info
    applied_timestamp = db.Column(db.DateTime)
    applied_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    applied_to_id = db.Column(db.Integer, db.ForeignKey('cube_card.id'))
    removed_timestamp = db.Column(db.DateTime)
    removed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Lock info
    locked_by_id = db.Column(db.Integer)
    locked_pack_id = db.Column(db.Integer)

    @staticmethod
    def get_for_pack(pack_id, user_id):
        return Scar.query.filter(
            Scar.locked_by_id == user_id,
            Scar.locked_pack_id == pack_id,
        ).all()

    def is_locked(self):
        return self.locked_by_id is not None

    def lock(self, pack_id, user_id):
        self.locked_by_id = user_id
        self.locked_pack_id = pack_id
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def lock_random_scars(pack_id, user_id, count):
        scars = Scar.query.filter(Scar.locked_by_id == None).all()
        random.shuffle(scars)
        scars = scars[:count]

        for scar in scars:
            scar.lock(pack_id, user_id)

        return scars
    
    def unlock(self, commit=True):
        self.locked_by_id = None
        self.locked_pack_id = None

        if commit:
            db.session.add(self)
            db.session.commit()


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cube_id = db.Column(db.Integer, db.ForeignKey('cube.id'))

    # Content info
    name = db.Column(db.Text)
    conditions = db.Column(db.Text)
    unlock = db.Column(db.Text)
    multiunlock = db.Column(db.Boolean)
    version = db.Column(db.Integer, default=1)

    # Creation info
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Unlock info
    unlocked_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    unlocked_timestamp = db.Column(db.DateTime)
    finalized_timestamp = db.Column(db.DateTime)

    def available(self):
        return self.unlocked_by_id is None

    def unlock_lines(self):
        return [x.strip() for x in self.unlock.split('\n') if x.strip()]
