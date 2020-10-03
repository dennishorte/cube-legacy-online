from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from app import db
from app import login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    slack_id = db.Column(db.String(50))
    
    cards_added = db.relationship('Card', backref='added_by')
    scars_applied = db.relationship('Scar', backref='added_by')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)    


@login.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    added_by_id= db.Column(db.Integer, db.ForeignKey('user.id'))

    scars = db.relationship('Scar', backref='card')

    def __repr__(self):
        return '<Card {}:{}>'.format(self.name, self.id)


class Scar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'))
    added_by_id= db.Column(db.Integer, db.ForeignKey('user.id'))
    text=db.Column(db.String(256))

    def __repr__(self):
        return '<Scar {}>'.format(self.id)

