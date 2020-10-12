import enum
import json
from datetime import datetime

from app import db
from app.models.user import *


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
    drafts = db.relationship('Draft', backref='cube')
    scars = db.relationship('Scar', backref='cube')

    def __repr__(self):
        return '<Cube {}>'.format(self.name)

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
        return [x['image_url'] for x in self.card_faces() if 'image_url' in x]

    def card_faces(self):
        return self.get_json()['card_faces']

    @classmethod
    def from_base_card(cls, cube_id, base_card, added_by):
        return CubeCard(
            version=1,
            cube_id=cube_id,
            base_id=base_card.id,
            json=base_card.json,
            added_by_id=added_by.id,
        )

    def update(self, new_json, edited_by, comment):
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
            db.session.commit()

            return True  # Changes detected and card updated

        else:
            return False  # No change detected


class Scar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cube_id = db.Column(db.Integer, db.ForeignKey('cube.id'))

    # Content info
    text = db.Column(db.String(64))
    restrictions = db.Column(db.String(64), default='')
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
