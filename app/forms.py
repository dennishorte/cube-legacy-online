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


class AddCardsForm(FlaskForm):
    cardnames = TextAreaField('Cards to be added (1 per line)')
    add_as_starter = BooleanField('Add as a starter card, not as yourself')
    submit = SubmitField('Add Cards')


class EditMultiFaceCardForm(FlaskForm):
    face_0_name = StringField('Name')
    face_0_mana_cost = StringField('Mana Cost')
    face_0_image_url = TextAreaField('Image Url')
    face_0_type_line = StringField('Type Line')
    face_0_oracle_text = TextAreaField('Rules Text')
    face_0_power = StringField('Power')
    face_0_toughness = StringField('Toughness')
    face_0_loyalty = StringField('Loyalty')
    
    face_1_name = StringField('Name')
    face_1_mana_cost = StringField('Mana Cost')
    face_1_image_url = TextAreaField('Image Url')
    face_1_type_line = StringField('Type Line')
    face_1_oracle_text = TextAreaField('Rules Text')
    face_1_power = StringField('Power')
    face_1_toughness = StringField('Toughness')
    face_1_loyalty = StringField('Loyalty')

    comment = TextAreaField('Comment')
    
    layout = SelectField('Layout', choices=Layout.choices(), validators=[DataRequired()])
    update_as = SelectField('Update As')
    submit = SubmitField('Update')

    # Used when adding a scar in order to mark the scar as applied.
    scar_id = HiddenField('Scar ID')
    
    
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class NewCubeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    style = RadioField('Style', validators=[DataRequired()], choices=['standard', 'legacy'])
    submit = SubmitField('Create')


class NewDraftForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    cube = SelectField('Cube', validators=[DataRequired()])
    packsize = IntegerField('Pack Size', validators=[DataRequired()])
    numpacks = IntegerField('Number of Packs', validators=[DataRequired()])
    players = SelectMultipleField('Players', validators=[DataRequired()])
    submit = SubmitField('Create')


class NewAchievementForm(FlaskForm):
    name = StringField('Name')
    conditions = TextAreaField('Conditions')
    unlock = TextAreaField('Unlock Info')
    multiunlock = BooleanField('Is Multiunlock')
    submit = SubmitField('Create')


class NewScarForm(FlaskForm):
    text = TextAreaField('Scar Text', validators=[DataRequired()])
    restrictions = StringField('Restrictions')
    submit = SubmitField('Create')


class ResultForm(FlaskForm):
    user_id = HiddenField('user_id')
    wins = IntegerField('wins', validators=[Optional()])
    losses = IntegerField('losses', validators=[Optional()])
    draws = IntegerField('draws', validators=[Optional()])
    submit = SubmitField('update')
