import enum
import json
from datetime import datetime

from app import db
from app.models.user import *


class CubeEditType(enum.Enum):
    add = 0
    remove = 1


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

    # Foreign Keys
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    _cards = db.relationship('CubeCard', backref='cube')
    drafts = db.relationship('Draft', backref='cube')
    edits = db.relationship('CubeEditHistory', backref='cube')

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

class CubeEditHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    type = db.Column(db.Enum(CubeEditType))

    # Foreign Keys
    cube_id = db.Column(db.Integer, db.ForeignKey('cube.id'))
    card_id = db.Column(db.Integer, db.ForeignKey('cube_card.id'))

    def __repr__(self):
        return '<CubeEdit {}>'.format(self.id)


class CubeCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    version = db.Column(db.Integer)
    latest = db.Column(db.Boolean, default=True)
    json = db.Column(db.Text)
    
    # Foreign Keys
    cube_id = db.Column(db.Integer, db.ForeignKey('cube.id'))
    base_id = db.Column(db.Integer, db.ForeignKey('base_card.id'))
    added_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    edited_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    removed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    draft_cards = db.relationship('PackCard', backref='cube_card')

    def __repr__(self):
        return '<CubeCard {}>'.format(self.json['name'])

    def get_json(self):
        return json.loads(self.json)
    
    def set_json(self, json_obj):
        self.json = json.dumps(json_obj)

    @classmethod
    def from_base_card(cls, cube_id, base_card, added_by):
        base_json = json.loads(base_card.json)
        all_faces = base_json.get('faces', []) + [base_json]
        
        # Make the image url a top-level value.
        for face in all_faces:
            if 'image_uris' in face:
                face['image_url'] = face['image_uris']['normal']

        wanted_keys = (
            # Meta data
            'all_parts',
            'card_faces',
            'faces',
            'layout',
            'object',

            # Card data
            'cmc',
            'component',
            'flavor_text',
            'image_url',
            'loyalty',
            'mana_cost',
            'name',
            'oracle_text',
            'power',
            'toughness',
            'type_line',
        )

        # Remove unwanted keys
        for face in all_faces:
            face_keys = list(face.keys())
            for key in face_keys:
                if not key in wanted_keys:
                    del face[key]

        return CubeCard(
            version=1,
            cube_id=cube_id,
            base_id=base_card.id,
            json=json.dumps(base_json),
            added_by_id=added_by.id,
        )

    def update(self, new_json, edited_by):
        """
        Assuming any changes have been made in the JSON compared to this CubeCard,
        creates a copy of this cube card and adds it to the database as an old verison,
        and then updates this card with the new data. This preserves the card id for
        drafts, when cards will be edited during drafting.
        """
        if self.removed_by_id:
            raise ValueError("Can't edit a removed card.")
            
        if self.json != new_json:
            new_card = CubeCard(
                json=self.json,
                version=self.version + 1,
                cube_id=self.cube_id,
                base_id=self.base_id,
                added_by_id=self.added_by_id,
                edited_by=self.edited_by_id,
                latest=False,
            )

            self.json = new_json
            self.edited_by_id = edited_by.id
            
            db.session.add(new_card)
            db.session.add(self)
            db.session.commit()
