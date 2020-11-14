import enum
import functools
import json
import random
import re
from datetime import datetime

from app import db
from app.models.user import *
from app.util import card_diff
from app.util import card_util
from app.util import cockatrice
from app.util.card_util import color_sort_key
from app.util.enum import DraftFaceUp
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

    # If True, this cube is for administrative purposes (eg. basic lands)
    admin = db.Column(db.Boolean, default=False)

    # Foreign Keys
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    _cards = db.relationship('CubeCard', backref='cube')
    achievements = db.relationship('Achievement', backref='cube')
    drafts = db.relationship('Draft', backref='cube')
    factions= db.relationship('Faction', backref='cube')
    scars = db.relationship('Scar', backref='cube')

    def __repr__(self):
        return '<Cube {}>'.format(self.name)

    def achievements_avaiable(self):
        achs = [x for x in self.achievements if x.available()]
        achs.sort(key=lambda x: x.created_timestamp, reverse=True)
        return achs

    def achievements_completed(self):
        achs = [x for x in self.achievements if not x.available()]
        achs.sort(key=lambda x: x.unlocked_timestamp, reverse=True)
        return achs

    def age(self):
        age = datetime.utcnow() - self.timestamp
        years = age.days // 365
        days = age.days % 365

        if years > 0:
            return f"{years} years {days} days"
        else:
            return f"{days} days"

    @functools.lru_cache
    def cards(self):
        """
        Get only the latest version of the cards in the cube.
        """
        cards = CubeCard.query.filter(
            CubeCard.cube_id == self.id,
            CubeCard.latest == True,
            CubeCard.removed_by_id == None,
        ).all()
        cards.sort(key=lambda x: x.name())
        return cards

    def cards_added(self):
        cards = CubeCard.query.filter(
            CubeCard.cube_id == self.id,
            CubeCard.version == 1,
            CubeCard.removed_by_id == None,
        ).order_by(
            CubeCard.timestamp.desc()
        ).limit(20)
        return cards

    def cards_removed(self):
        cards = CubeCard.query.filter(
            CubeCard.cube_id == self.id,
            CubeCard.latest == True,
            CubeCard.removed_by_id != None,
        ).order_by(
            CubeCard.removed_by_timestamp.desc()
        ).all()
        return cards

    def cards_updated(self, limit=20):
        return CubeCard.query.filter(
            CubeCard.cube_id == self.id,
            CubeCard.removed_by_id == None,
            CubeCard.edited_by_id != None,
            CubeCard.id == CubeCard.latest_id,
        ).order_by(
            CubeCard.timestamp.desc(),
            CubeCard.id,
        ).limit(limit)

    def get_card_by_name(self, name):
        filtered = [x for x in self.cards() if x.name() == name]
        if not filtered:
            return None
        elif len(filtered) == 1:
            return filtered[0]
        else:
            return filtered

    def used_scars(self):
        used = [x for x in self.scars if x.applied_timestamp]
        used.sort(key=lambda x: x.applied_timestamp, reverse=True)
        return used


class CubeCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    version = db.Column(db.Integer)
    latest = db.Column(db.Boolean, default=True)
    json = db.Column(db.Text)
    comment = db.Column(db.Text)

    # True if created through the card_create form. False otherwise.
    is_original = db.Column(db.Boolean, default=False)

    # Group id: all versions of a single card have the same group id
    latest_id = db.Column(db.Integer)

    # Base id is only present if the card was imported from Scryfall. If it was added the
    # the card create form, it will be null.
    base_id = db.Column(db.Integer, db.ForeignKey('base_card.id'))
    cube_id = db.Column(db.Integer, db.ForeignKey('cube.id'))
    added_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    edited_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    removed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    removed_by_comment = db.Column(db.Text)
    removed_by_timestamp = db.Column(db.DateTime)

    # Relationships
    draft_cards = db.relationship('PackCard', backref='cube_card')
    linked_achs = db.relationship('AchievementLink', backref='card')
    scars = db.relationship('Scar', backref='applied_to')

    def __repr__(self):
        return '<CubeCard {}>'.format(self.get_json()['name'])

    def card_diff(self, face=None):
        # Deprecated. Use differ().
        return card_util.CardDiffer(self.original, self, face)

    def card_faces(self):
        return self.get_json()['card_faces']

    def cockatrice_name(self):
        data = self.get_json()
        return cockatrice._card_name(
            card_data=data,
            face_index=0,
            scarred=self.is_scarred(),
        )

    def draft_face_up(self):
        rules = self.oracle_text()
        may_pattern = r'[Mm]ay draft.*?face up'
        if re.search(may_pattern, rules):
            return DraftFaceUp.optional

        pattern = r'[Dd]raft.*?face up'
        if re.search(pattern, rules):
            return DraftFaceUp.true

        else:
            return DraftFaceUp.false

    def differ(self):
        return card_diff.CardDiffer(self.original, self)

    def days_since_last_edit(self):
        return (datetime.utcnow() - self.timestamp).days

    @classmethod
    def from_base_card(cls, cube_id, base_card, added_by):
        return CubeCard(
            version=1,
            cube_id=cube_id,
            base_id=base_card.id,
            json=base_card.json,
            added_by_id=added_by.id,
        )

    @functools.lru_cache
    def get_json(self):
        return json.loads(self.json)

    def image_back(self):
        images = self.image_urls()
        if len(images) > 1:
            return images[1]

    def image_front(self):
        return self.image_urls()[0]

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

    @functools.cached_property
    def original(self):
        return CubeCard.query.filter(
            CubeCard.version == 1,
            CubeCard.latest_id == self.latest_id,
        ).first()

    @functools.cached_property
    def removed_by(self):
        if not self.removed_by_id:
            return None
        else:
            return User.query.get(self.removed_by_id).name

    def set_json(self, json_obj):
        self.json = json.dumps(json_obj)

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
                latest_id=self.id,
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
            self.timestamp = datetime.utcnow()

            db.session.add(new_card)
            db.session.add(self)

            if commit:
                db.session.commit()

            return True  # Changes detected and card updated

        else:
            return False  # No change detected

    def versions(self):
        return CubeCard \
            .query \
            .filter(CubeCard.latest_id == self.latest_id) \
            .order_by(CubeCard.version.desc())

    def cmc(self):
        cost = 0
        cost += card_util.cmc_from_string(self.card_faces()[0]['mana_cost'])

        if self.layout() == Layout.split.name:
            cost += card_util.cmc_from_string(self.card_faces()[1]['mana_cost'])

        return cost

    def color_identity(self):
        pattern = r"{(.*?)}"
        identity = set()
        for face in self.card_faces():
            texts = [face['mana_cost']] + re.findall(pattern, face['oracle_text'])
            for text in texts:
                for ch in face['mana_cost'].upper():
                    if ch in 'WUBRG':
                        identity.add(ch)

        identity = sorted(identity, key=color_sort_key)
        identity = ''.join(identity)

        return identity

    def has_type(self, card_type):
        return card_type.lower() in self.card_faces()[0].get('type_line', '').lower()

    def layout(self):
        return self.get_json()['layout']

    def name(self):
        return self.get_json().get('name', 'NO_NAME')

    def is_creature(self):
        return 'creature' in self.card_faces()[0].get('type_line', '').lower()

    def is_land(self):
        return 'land' in self.card_faces()[0].get('type_line', '').lower()

    def oracle_text(self):
        return self.get_json()['oracle_text']

    def type_line(self):
        return self.get_json().get('type_line', 'NO_TYPE')


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
        from app.models.draft import Pack
        pack = Pack.query.get(pack_id)

        scars = Scar.random_scars(pack.draft.cube_id, count)
        for scar in scars:
            scar.lock(pack_id, user_id)

        return scars

    @staticmethod
    def random_scars(cube_id, count):
        scars = Scar.query.filter(
            Scar.cube_id == cube_id,
            Scar.applied_to_id == None,
            Scar.locked_by_id == None,
        ).all()
        random.shuffle(scars)
        return scars[:count]

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
    multiunlock = db.Column(db.Boolean)
    version = db.Column(db.Integer, default=1)
    unlock_json = db.Column(db.Text)

    # Creation info
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Unlock info
    unlocked_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    unlocked_timestamp = db.Column(db.DateTime)
    finalized_timestamp = db.Column(db.DateTime)
    story = db.Column(db.Text)

    # Deprecated (use unlock_json instead)
    unlock = db.Column(db.Text)

    # Relationships
    linked_cards = db.relationship('AchievementLink', backref='achievement')
    linked_drafts = db.relationship('AchievementDraftLink', backref='ach')
    starred = db.relationship('AchievementStar', backref='achievement')

    def available(self):
        return self.unlocked_by_id is None

    def clone(self):
        latest_version = Achievement.query.filter(
            Achievement.name == self.name,
            Achievement.cube_id == self.cube_id,
        ).order_by(
            Achievement.version.desc()
        ).first()

        ach = Achievement()
        ach.name = self.name
        ach.conditions = self.conditions
        ach.multiunlock = self.multiunlock
        ach.unlock_json = self.unlock_json
        ach.created_by_id = self.created_by_id
        ach.version = latest_version.version + 1
        ach.cube_id = self.cube_id
        return ach

    def full_name(self):
        return f"{self.name} v.{self.version}"

    def get_json(self):
        return json.loads(self.unlock_json)

    def set_json(self, data):
        self.unlock_json = json.dumps(data)

    def starred_by_user(self, user):
        if not user:
            return False

        for star in self.starred:
            if star.user_id == user.id:
                return True

        return False

    def unlock_lines(self):
        return [x.strip() for x in self.unlock.split('\n') if x.strip()]


class AchievementLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cube_card.id'))
    ach_id = db.Column(db.Integer, db.ForeignKey('achievement.id'))


class AchievementStar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ach_id = db.Column(db.Integer, db.ForeignKey('achievement.id'))

    def __repr__(self):
        return f"AchievementStar({self.ach_id},{self.user_id})"


class Faction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cube_id = db.Column(db.Integer, db.ForeignKey('cube.id'))
    name = db.Column(db.String(128))
    desc = db.Column(db.Text)  # Description
    memb = db.Column(db.Text)  # Membership criteria
    note = db.Column(db.Text)  # Notes

    def age(self):
        age = datetime.utcnow() - self.created_at
        years = age.days // 365
        days = age.days % 365

        if years > 0:
            return f"{years} years {days} days"
        else:
            return f"{days} days"
