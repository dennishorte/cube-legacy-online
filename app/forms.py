from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import PasswordField
from wtforms import RadioField
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Length

from app.util.enum import Layout


class AddCardsForm(FlaskForm):
    cardnames = TextAreaField('Cards to be added (1 per line)')
    add_as_starter = BooleanField('Add as a starter card, not as yourself')
    submit = SubmitField('Add Cards')


class EditCardForm(FlaskForm):
    TYPE = 'single'
    
    name = StringField('Name', validators=[DataRequired()])
    manacost = StringField('Mana Cost', validators=[DataRequired()])
    imageurls = TextAreaField('Image Url', validators=[DataRequired()])
    typeline = StringField('Type Line', validators=[DataRequired()])
    rulestext = TextAreaField('Rules Text')
    pt_loyalty = StringField('p/t or loyalty')
    layout = SelectField('Layout', choices=Layout.choices(), validators=[DataRequired()])
    submit = SubmitField('Update')


class EditMultiFaceCardForm(FlaskForm):
    TYPE = 'multi'
    
    front_name = StringField('Name', validators=[DataRequired()])
    front_mana_cost = StringField('Mana Cost', validators=[DataRequired()])
    front_image_url = TextAreaField('Image Url', validators=[DataRequired()])
    front_type_line = StringField('Type Line', validators=[DataRequired()])
    front_rules_text = TextAreaField('Rules Text')
    front_power = StringField('Power')
    front_toughness = StringField('Toughness')
    front_loyalty = StringField('Loyalty')
    
    back_name = StringField('Name')
    back_mana_cost = StringField('Mana Cost')
    back_image_url = TextAreaField('Image Url')
    back_type_line = StringField('Type Line')
    back_rules_text = TextAreaField('Rules Text')
    back_power = StringField('Power')
    back_toughness = StringField('Toughness')
    back_loyalty = StringField('Loyalty')

    layout = SelectField('Layout', choices=Layout.choices(), validators=[DataRequired()])
    submit = SubmitField('Update')
    
    
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


class NewScarForm(FlaskForm):
    text = TextAreaField('Scar Text', validators=[DataRequired()])
    restrictions = StringField('Restrictions')
    submit = SubmitField('Create')
