from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import PasswordField
from wtforms import RadioField
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Optional

from app.util.enum import Layout
from app.util.string import normalize_newlines


class AddCardsForm(FlaskForm):
    cardnames = TextAreaField('Cards to be added (1 per line)')
    add_as_starter = BooleanField('Add as a starter card, not as yourself')
    submit = SubmitField('Add Cards')


class CardRarityForm(FlaskForm):
    rarities = TextAreaField('Rarities to set (1 per line: <name>\t<rarity>)')
    submit = SubmitField('Set Rarities')


class GameDeckReadyForm(FlaskForm):
    maindeck_ids = HiddenField('maindeck')
    sideboard_ids = HiddenField('sideboard')
    basics_list = HiddenField('basics')
    submit = SubmitField('Ready!')


class DeckSelectorForm(FlaskForm):
    deck = SelectField('Deck')
    submit = SubmitField('Load Deck')

    @staticmethod
    def factory(user_id):
        from app.models.deck import Deck
        decks = Deck.query.filter(Deck.user_id == user_id).order_by(Deck.name).all()
        decks = [('none', '')] + [(str(x.id), x.name) for x in decks]

        form = DeckSelectorForm()
        form.deck.choices = decks

        return form


class EditMultiFaceCardForm(FlaskForm):
    face_0_name = StringField('Name')
    face_0_mana_cost = StringField('Mana Cost')
    face_0_image_url = TextAreaField('Image Url')
    face_0_type_line = StringField('Type Line')
    face_0_oracle_text = TextAreaField('Rules Text')
    face_0_flavor_text = TextAreaField('Flavor Text')
    face_0_power = StringField('Power')
    face_0_toughness = StringField('Toughness')
    face_0_loyalty = StringField('Loyalty')

    face_1_name = StringField('Name')
    face_1_mana_cost = StringField('Mana Cost')
    face_1_image_url = TextAreaField('Image Url')
    face_1_type_line = StringField('Type Line')
    face_1_oracle_text = TextAreaField('Rules Text')
    face_1_flavor_text = TextAreaField('Flavor Text')
    face_1_power = StringField('Power')
    face_1_toughness = StringField('Toughness')
    face_1_loyalty = StringField('Loyalty')

    comment = TextAreaField('Comment')

    layout = SelectField('Layout', choices=Layout.choices(), validators=[DataRequired()])
    update_as = SelectField('Update As')
    submit = SubmitField('Update')

    # Used when adding a scar in order to mark the scar as applied.
    scar_id = HiddenField('Scar ID')

    def group_fields(self):
        """Group the form fields to allow programatic access."""
        self.faces = [
            {
                'name': self.face_0_name,
                'mana_cost': self.face_0_mana_cost,
                'image_url': self.face_0_image_url,
                'type_line': self.face_0_type_line,
                'oracle_text': self.face_0_oracle_text,
                'flavor_text': self.face_0_flavor_text,
                'power': self.face_0_power,
                'toughness': self.face_0_toughness,
                'loyalty': self.face_0_loyalty,
            },
            {
                'name': self.face_1_name,
                'mana_cost': self.face_1_mana_cost,
                'image_url': self.face_1_image_url,
                'type_line': self.face_1_type_line,
                'oracle_text': self.face_1_oracle_text,
                'flavor_text': self.face_1_flavor_text,
                'power': self.face_1_power,
                'toughness': self.face_1_toughness,
                'loyalty': self.face_1_loyalty,
            },
        ]


class FinalizeAchievementForm(FlaskForm):
    story = TextAreaField('Tell the Story of This Achievement', validators=[DataRequired()])
    submit = SubmitField("I've done all the things")


class LinkAchievemetAndCardForm(FlaskForm):
    card = SelectField('Card')
    achievement = SelectField('Achievement')
    submit = SubmitField('Link')

    @staticmethod
    def factory(cube_id, card=None, achievement=None):
        from app.models.cube import Achievement
        from app.models.cube import CubeCard

        form = LinkAchievemetAndCardForm()

        if card is None:
            cards = CubeCard.query.filter(
                CubeCard.cube_id == cube_id,
                CubeCard.removed_by_timestamp == None,
            ).all()
            cards.sort(key=lambda x: x.name())
            form.card.choices = [(x.id, x.name()) for x in cards]
        else:
            form.card.choices = [(card.id, card.name())]

        if achievement is None:
            achs = Achievement.query.filter(
                Achievement.cube_id == cube_id,
                Achievement.unlocked_timestamp == None,
            ).all()
            achs.sort(key=lambda x: x.name)
            form.achievement.choices = [(x.id, x.name) for x in achs]
        else:
            form.achievement.choices = [(achievement.id, achievement.name)]

        return form


class LoadDraftDeckForm(FlaskForm):
    draft = SelectField('Draft')
    submit = SubmitField('Load Cards')

    @staticmethod
    def factory(user_id):
        from app.models.user import User
        user = User.query.get(user_id)
        drafts = [(x.id, x.draft.name) for x in user.draft_seats]

        form = LoadDraftDeckForm()
        form.draft.choices = drafts

        return form


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class NewCubeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    style = RadioField('Style', validators=[DataRequired()], choices=['standard', 'legacy', 'set'])
    submit = SubmitField('Create')


class NewDraftForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    cube = SelectField('Cube', validators=[DataRequired()])
    packsize = IntegerField('Pack Size', validators=[DataRequired()])
    numpacks = IntegerField('Number of Packs', validators=[DataRequired()])
    scar_rounds = StringField('Scar Rounds (eg. 0,3)')
    players = SelectMultipleField('Players', validators=[DataRequired()])
    submit = SubmitField('Create')

    @staticmethod
    def factory():
        from app.models.cube import Cube
        from app.models.user import User

        cubes = [x.name for x in Cube.query.order_by('name')]
        users = [(x.name, x.name) for x in User.query.order_by('name') if x.name != 'starter']

        form = NewDraftForm()
        form.cube.choices = cubes
        form.players.choices = users

        return form


class NewSetDraftForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    cube = SelectField('Cube', validators=[DataRequired()])
    style = SelectField('Style', validators=[DataRequired()], choices=['standard', 'commander'])
    players = SelectMultipleField('Players', validators=[DataRequired()])
    submit = SubmitField('Create')

    @staticmethod
    def factory():
        from app.models.cube import Cube
        from app.models.user import User

        cubes = [x.name for x in Cube.query.order_by('name') if x.style_a == 'set']
        users = [(x.name, x.name) for x in User.query.order_by('name') if x.name != 'starter']

        form = NewSetDraftForm()
        form.cube.choices = cubes
        form.players.choices = users

        return form


class NewGameForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    players = SelectMultipleField('Players', validators=[DataRequired()])
    submit = SubmitField('Create')

    @staticmethod
    def factory():
        from app.models.user import User
        user_names = [(str(x.id), x.name) for x in User.query.order_by('name') if x.name != 'starter']
        form = NewGameForm()
        form.players.choices = user_names
        return form


class NewAchievementForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    conditions = TextAreaField('How to Unlock', validators=[DataRequired()])

    unlock_1_timing = StringField('Unlock 1 Timing')
    unlock_1_text = TextAreaField('Unlock 1 Description')

    unlock_2_timing = StringField('Unlock 2 Timing')
    unlock_2_text = TextAreaField('Unlock 2 Description')

    unlock_3_timing = StringField('Unlock 3 Timing')
    unlock_3_text = TextAreaField('Unlock 3 Description')

    unlock_4_timing = StringField('Unlock 4 Timing')
    unlock_4_text = TextAreaField('Unlock 4 Description')

    unlock_5_timing = StringField('Unlock 5 Timing')
    unlock_5_text = TextAreaField('Unlock 5 Description')

    cube_id = HiddenField('Cube Id')  # Used when creating a new achievement
    update_id = HiddenField('Update Id')  # Used when updating an existing achievement

    multiunlock = BooleanField('Is Multiunlock')
    update_as = SelectField('Create As')
    submit = SubmitField('Create')

    def group_fields(self):
        self.unlocks = [
            {
                'timing': self.unlock_1_timing,
                'text': self.unlock_1_text,
            },
            {
                'timing': self.unlock_2_timing,
                'text': self.unlock_2_text,
            },
            {
                'timing': self.unlock_3_timing,
                'text': self.unlock_3_text,
            },
            {
                'timing': self.unlock_4_timing,
                'text': self.unlock_4_text,
            },
            {
                'timing': self.unlock_5_timing,
                'text': self.unlock_5_text,
            },
        ]

    def fill_from_json_list(self, json_list):
        if not self.unlocks:
            self.group_fields()

        assert len(json_list) <= len(self.unlocks), "Too many values to load."

        for i in range(len(self.unlocks)):
            group = self.unlocks[i]
            datum = json_list[i]

            group['timing'].data = datum['timing']
            group['text'].data = datum['text']

    def unlock_json(self):
        flat = []
        for group in self.unlocks:
            flat.append({
                'timing': normalize_newlines(group['timing'].data.strip()),
                'text': normalize_newlines(group['text'].data.strip()),
            })
        return flat


class NewFactionForm(FlaskForm):
    id = HiddenField('Faction ID')
    name = StringField('Faction Name')
    desc = TextAreaField('Description')
    memb = TextAreaField('Membership Criteria')
    note = TextAreaField('Notes')
    submit = SubmitField('Create/Update')


class NewScarForm(FlaskForm):
    text = TextAreaField('Scar Text', validators=[DataRequired()])
    restrictions = StringField('Restrictions')
    update_id = StringField('ID of Scar to Update')
    update_as = SelectField('Create As')
    submit = SubmitField('Create')


class PackMakerForm(FlaskForm):
    obj_type = SelectField('Type', choices=['Cards', 'Dead Interns'])
    cube_name = SelectField('Cube')
    count = SelectField('Count', choices=range(1, 16))
    submit = SubmitField('Make Pack')

    @staticmethod
    def factory(count=None):
        from app.models.cube import Cube
        form = PackMakerForm()
        form.cube_name.choices = [x.name for x in Cube.query.order_by('name')]
        if count:
            form.count.data = str(count)
        return form


class RandomScarsForm(FlaskForm):
    count = SelectField('Count', choices=range(1, 10))
    submit = SubmitField('Random Scars')


class ReallyUnlockForm(FlaskForm):
    submit = SubmitField('I Earned this Man')


class RemoveCardForm(FlaskForm):
    comment = TextAreaField('Reason for Removal')
    submit = SubmitField('Remove Card from Cube')


class ResultForm(FlaskForm):
    user_id = HiddenField('user_id')
    wins = IntegerField('wins', validators=[Optional()])
    losses = IntegerField('losses', validators=[Optional()])
    draws = IntegerField('draws', validators=[Optional()])
    submit = SubmitField('update')


class SaveDeckListForm(FlaskForm):
    name = StringField('Deck Name', validators=[DataRequired()])
    decklist = TextAreaField('Deck List', validators=[DataRequired()])
    submit = SubmitField('Save')


class SelectDraftForm(FlaskForm):
    draft = SelectField('Draft')
    submit = SubmitField('Select')

    def factory():
        from app.models.draft import Draft
        drafts = Draft.query.order_by(Draft.timestamp.desc()).all()
        form = SelectDraftForm()
        form.draft.choices = [(0, '')] + [(x.id, x.name) for x in drafts]
        return form


class UseScarForm(FlaskForm):
    scar_id = IntegerField('Scar ID')
    card_name = SelectField('Card Name')
    submit = SubmitField('Use')
