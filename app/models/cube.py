import enum
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

    # Relationships
    cards = db.relationship('CubeCard', backref='base')

    def __repr__(self):
        return '<BaseCard {}>'.format(self.name)
    

class Cube(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    active = db.Column(db.Boolean, index=True)

    # Relationships
    cards = db.relationship('CubeCard', backref='cube')
    edits = db.relationship('CubeEditHistory', backref='cube')

    def __repr__(self):
        return '<Cube {}>'.format(self.name)


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
    active = db.Column(db.Boolean, index=True)
    json = db.Column(db.Text)
    
    # Foreign Keys
    cube_id = db.Column(db.Integer, db.ForeignKey('cube.id'))
    base_id = db.Column(db.Integer, db.ForeignKey('base_card.id'))

    # Relationships
    versions = db.relationship('CubeCardVersionHistory', backref='card')

    def __repr__(self):
        return '<CubeCard {}>'.format(self.json['name'])

    
class CubeCardVersionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    json = db.Column(db.Text)

    # Foreign Keys
    card_id = db.Column(db.Integer, db.ForeignKey('cube_card.id'))

    def __repr__(self):
        return '<CubeCardVersion {} id:{}>'.format(self.json['name'], id)
