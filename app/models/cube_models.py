import enum
import json
import random
import re
from datetime import datetime

from app import db
from app.models.user_models import *
from app.util import card_util
from app.util import cockatrice
from app.util.card_diff import CardDiffer
from app.util.card_util import color_sort_key
from app.util.enum import DraftFaceUp
from app.util.enum import Layout


class CubeStyle(enum.Enum):
    """
    DEPRECATED

    use cube.style_a, which is a string, instead
    """
    standard = 1
    legacy = 2
    set = 3


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
    style_a = db.Column(db.String(16))
    set_code = db.Column(db.String(16))

    # If True, this cube is for administrative purposes (eg. basic lands)
    admin = db.Column(db.Boolean, default=False)

    # Foreign Keys
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    _cards = db.relationship('CubeCard', backref='cube')
    achievements = db.relationship('Achievement', backref='cube')
    drafts = db.relationship('Draft', backref='cube')
    scars = db.relationship('Scar', backref='cube')
    searches = db.relationship('CubeSearch', backref='cube')

    def __repr__(self):
        return '<Cube {}>'.format(self.name)

    def achievements_wrapper(self):
        from app.util.achievements_wrapper import AchievementsWrapper
        return AchievementsWrapper.from_cube(self)

    def age(self):
        age = datetime.utcnow() - self.timestamp
        years = age.days // 365
        days = age.days % 365

        if years > 0:
            return f"{years} years {days} days"
        else:
            return f"{days} days"

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
        return CubeCard.query.filter(
            CubeCard.cube_id == self.id,
            CubeCard.name_tmp == name,
        ).first()

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

    # Duplicate of what's in the JSON, but so often desired for querying that it's cached here.
    name_tmp = db.Column(db.String(128))

    # JSON cache of diff between this version and the original version
    diff = db.Column(db.Text)

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

    # Cached pick info (updated each time the card is picked in a draft)
    pick_info_count = db.Column(db.Integer, default=0)
    pick_info_avg = db.Column(db.Float, default=0)

    # Relationships
    draft_cards = db.relationship('PackCard', backref='cube_card')
    linked_achs = db.relationship('AchievementLink', backref='card')
    scars = db.relationship('Scar', backref='applied_to')

    _json_cached = None

    def __repr__(self):
        return '<CubeCard {}>'.format(self.name())

    def card_face(self, index):
        faces = self.card_faces()
        if len(faces) <= index:
            return None
        else:
            return faces[index]

    def card_faces(self):
        return self.get_json()['card_faces']

    def cockatrice_name(self):
        data = self.get_json()
        return cockatrice._card_name(
            card_data=data,
            face_index=0,
            scarred=self.is_scarred(),
        )

    def copy(self):
        new_card = CubeCard()
        new_card.id = None
        new_card.timestamp = self.timestamp
        new_card.version = self.version
        new_card.latest = self.latest
        new_card.json = self.json
        new_card.comment = self.comment
        new_card.name_tmp = self.name_tmp
        new_card.diff = self.diff
        new_card.is_original = self.is_original
        new_card.latest_id = self.latest_id
        new_card.base_id = self.base_id
        new_card.cube_id = self.cube_id
        new_card.added_by_id = self.added_by_id
        new_card.edited_by_id = self.edited_by_id
        new_card.removed_by_id = self.removed_by_id
        new_card.removed_by_comment = self.removed_by_comment
        new_card.removed_by_timestamp = self.removed_by_timestamp
        new_card.pick_info_count = self.pick_info_count
        new_card.pick_info_avg = self.pick_info_avg
        return new_card

    def copy_to(self, cube_id):
        copy = self.copy()
        copy.timestamp = datetime.utcnow()
        copy.version = 0
        copy.diff = None
        copy.latest = True
        copy.cube_id = cube_id
        copy.removed_by_id = None
        copy.removed_by_comment = None
        copy.removed_by_timestamp = None
        copy.pick_info_count = 0
        copy.pick_info_avg = 0
        db.session.add(copy)
        db.session.commit()

        copy.latest_id = copy.id
        db.session.add(copy)
        db.session.commit()

        return copy

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

    def days_since_last_edit(self):
        return (datetime.utcnow() - self.timestamp).days

    def flatten(self):
        self.is_original = True
        self.version = 1
        self.diff = None

        db.session.add(self)

        all_versions = CubeCard.query.filter(CubeCard.latest_id == self.latest_id).all()
        for dead in all_versions:
            if dead.id == self.id:
                continue

            db.session.delete(dead)

        db.session.commit()


    @classmethod
    def from_base_card(cls, cube_id, base_card, added_by):
        data = base_card.get_json()
        return CubeCard(
            version=1,
            cube_id=cube_id,
            base_id=base_card.id,
            json=base_card.json,
            added_by_id=added_by.id,
            name_tmp=data['name'],
        )

    def get_diff(self, force_update=False):
        if not self.diff or force_update:
            differ = CardDiffer(self.original, self)
            self.diff = json.dumps(differ.json_summary())
            db.session.add(self)
            db.session.commit()

        return json.loads(self.diff)

    def get_json(self, force_update=False):
        if not self._json_cached or force_update:
            data = json.loads(self.json)
            self._json_cached = data

            if self.cube.style_a == 'legacy':
                # Get diff
                diff = self.get_diff()
                for i in range(len(data['card_faces'])):
                    rules_diff = diff['faces'][i]['oracle_text']
                    face = data['card_faces'][i]
                    face['scarred_oracle_text'] = rules_diff['plussed']
                    face['scarred'] = rules_diff['is_changed']

                # Get linked achievements
                for ach in self.linked_achievements():
                    data['card_faces'][0].setdefault('achievements', []).append({
                        'name': ach.name,
                        'conditions': ach.conditions,
                        'version': ach.version,
                        'xp': ach.xp,
                    })

                # Get pick info
                if self.pick_info_count is None:
                    self.pick_info_count = 0
                    self.pick_info_avg = 0
                data['card_faces'][0]['pick_info'] = {
                    'num_picks': self.pick_info_count,
                    'average_pick': '{:.1f}'.format(self.pick_info_avg),
                }

                # Replace name in rules text
                for i in range(len(data['card_faces'])):
                    name_diff = diff['faces'][i]['name']
                    if name_diff['is_changed'] and name_diff['original']:
                        new_name = name_diff['latest']
                        old_name = name_diff['original']
                        card_face = data['card_faces'][i]
                        card_face['scarred_oracle_text'] = card_face['scarred_oracle_text'].replace(old_name, new_name)

        return self._json_cached

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
        return self.version and self.version > 1 and self.cube.style_a == 'legacy'

    def linked_achievements(self):
        return [x.achievement for x in self.linked_achs if not x.achievement.unlocked_by_id]

    @property
    def original(self):
        orig = CubeCard.query.filter(
            CubeCard.latest_id == self.latest_id,
        ).order_by(CubeCard.version).first()

        if not orig:
            raise RuntimeError(f"No original card found for {self.name()}")

        return orig

    def pick_info_update(self, commit=True):
        from app.util import cube_data
        info = cube_data.CardData(self).pick_info
        self.pick_info_count = info.num_picks()

        if self.pick_info_count:
            self.pick_info_avg = info.average_pick()
        else:
            self.pick_info_avg = 0

        db.session.add(self)

        if commit:
            db.session.commit()

    def set_json(self, json_obj):
        self.name_tmp = json_obj['name']
        self.json = json.dumps(json_obj)

    def soft_update(self, new_json):
        return self.update(
            new_json = new_json,
            edited_by = None,
            comment = None,
            commit = False,
            new_version = False,
        )

    def update(self, new_json, edited_by, comment, commit=True, new_version=True):
        """
        Assuming any changes have been made in the JSON compared to this CubeCard,
        creates a copy of this cube card and adds it to the database as an old verison,
        and then updates this card with the new data. This preserves the card id for
        drafts, when cards will be edited during drafting.

        if commit is true, commit to db immediately. Otherwise, just add to session.
        if new_version is false, don't create a new version, and just update the json data.
          - Typically used when updating the json schema.
        """
        if self.removed_by_id:
            raise ValueError("Can't edit a removed card.")

        if self.get_json() != new_json:

            if new_version:
                # Create a copy of this card as a non-latest version.
                new_card = self.copy()
                new_card.latest = False
                new_card.diff = None
                db.session.add(new_card)

                # Update this card with the new data.
                self.version += 1
                self.edited_by_id = edited_by.id
                self.comment = comment
                self.timestamp = datetime.utcnow()

            self.json = json.dumps(new_json)
            self.name_tmp = new_json['name']
            self.diff = None
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
            if face.get('color_override'):
                identity.add(face.get('color_override'))

            else:
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
        return self.name_tmp

    def is_creature(self):
        return 'creature' in self.card_faces()[0].get('type_line', '').lower()

    def is_land(self):
        return 'land' in self.card_faces()[0].get('type_line', '').lower()

    def oracle_text(self):
        return self.get_json()['oracle_text']

    def rarity(self):
        return self.get_json()['rarity']

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
    locked_draft_id = db.Column(db.Integer)

    def is_locked(self):
        return self.locked_by_id is not None

    @staticmethod
    def draft_v2_get(draft_id, user_id):
        return Scar.query.filter(
            Scar.locked_by_id == user_id,
            Scar.locked_draft_id == draft_id,
        ).all()

    @staticmethod
    def draft_v2_lock(draft_id, cube_id, user_id, count):
        scars = Scar.random_scars(cube_id, count)
        for scar in scars:
            scar.locked_by_id = user_id
            scar.locked_draft_id = draft_id
            db.session.add(scar)

        db.session.commit()
        return scars

    @staticmethod
    def draft_v2_unlock(draft_id, user_id):
        locked = Scar.query.filter(
            Scar.locked_draft_id == draft_id,
            Scar.locked_by_id == user_id
        ).all()

        for scar in locked:
            scar.locked_by_id = None
            scar.locked_draft_id = None
            db.session.add(scar)

        db.session.commit()

    @staticmethod
    def random_scars(cube_id, count):
        scars = Scar.query.filter(
            Scar.cube_id == cube_id,
            Scar.applied_to_id == None,
            Scar.locked_by_id == None,
        ).all()
        random.shuffle(scars)
        return scars[:count]


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cube_id = db.Column(db.Integer, db.ForeignKey('cube.id'))

    # Content info
    name = db.Column(db.Text)
    conditions = db.Column(db.Text)
    multiunlock = db.Column(db.Boolean, default=False)
    version = db.Column(db.Integer, default=1)
    unlock_json = db.Column(db.Text)
    xp = db.Column(db.Integer, default=0)

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
    linked_drafts_v2 = db.relationship('DraftV2AchievementLink', backref='ach')
    starred = db.relationship('AchievementStar', backref='achievement')

    def unlock_date(self):
        pass

    def available(self):
        return self.unlocked_by_id is None

    def clone(self):
        all_open_versions = Achievement.query.filter(
            Achievement.name == self.name,
            Achievement.cube_id == self.cube_id,
            Achievement.unlocked_by_id == None,
        ).first()

        if all_open_versions:
            # There is already an active version of this achievement.
            # So, don't make another.
            return

        latest_version = Achievement.query.filter(
            Achievement.name == self.name,
            Achievement.cube_id == self.cube_id,
        ).order_by(
            Achievement.version.desc()
        ).first()

        ach = Achievement()
        ach.xp = 1
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

    def starred_by_user(self, user_id):
        if not user_id:
            return False

        if hasattr(user_id, 'id'):
            user_id = user_id.id

        for star in self.starred:
            if star.user_id == user_id:
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


class CubeSearch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cube_id = db.Column(db.Integer, db.ForeignKey('cube.id'))
    serialized = db.Column(db.Text, nullable=False)
    name = db.Column(db.String(64))

    @staticmethod
    def cleanup():
        CubeSearch.query.filter(CubeSearch.name == None).delete()
        db.session.commit()

    def json(self):
        return json.loads(self.serialized)

    def execute(self, card_list):
        return [x for x in card_list if self.match(x)]

    def match(self, card):
        """
        name: [{
          operator: 'and',
          key: 'wolf'
        },]
        power: [{
          operator: '>',
          key: 3
        }]
        """
        data = card.get_json()

        for field, filters in self.json().items():
            value = data.get(field, '')

            if not value:
                value = data['card_faces'][0].get(field, '')

            if isinstance(value, str):
                value = value.lower()

            for f in filters:
                if not self._apply_filter(f, value):
                    return False

        return True

    def _apply_filter(self, f, value):
        op = f['operator'].lower()
        key = f['key']

        if isinstance(key, str):
            key = key.lower()

        if op == 'and':
            return key in value
        elif op == 'not':
            return key not in value

        # All other relations are numerical
        else:
            if value == '':
                # This card doesn't have a matching value. eg. instants don't have power
                return False
            elif value == '*':
                value = 0

            key = float(key)
            value = float(value)

            if op == '=':
                return key == value
            elif op == '<=':
                return value <= key
            elif op == '>=':
                return value >= key
            else:
                raise ValueError(f"Unknown operator: {op}")
