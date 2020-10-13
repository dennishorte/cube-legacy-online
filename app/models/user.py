from flask_login import UserMixin
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from app import db
from app import login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    slack_id = db.Column(db.String(50))

    cubes = db.relationship('Cube', backref='created_by')
    draft_seats = db.relationship('Seat', backref='user')
    match_results = db.relationship('MatchResult', backref='user')
    
    scars_created = db.relationship('Scar', backref='created_by', foreign_keys='Scar.created_by_id')
    scars_added = db.relationship('Scar', backref='applied_by', foreign_keys='Scar.applied_by_id')
    scars_removed = db.relationship('Scar', backref='removed_by', foreign_keys='Scar.removed_by_id')

    def __repr__(self):
        return '<User {}>'.format(self.name)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()
