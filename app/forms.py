from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Length


class AddCardsForm(FlaskForm):
    cardnames = TextAreaField('Cards to be added (1 per line)')
    submit = SubmitField('Add Cards')
    

class EditCardForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=63)])
    manacost = StringField('Mana Cost', validators=[DataRequired(), Length(max=32)])
    imageurl = StringField('Image Url', validators=[DataRequired(), Length(max=255)])
    typeline = StringField('Type Line', validators=[DataRequired(), Length(max=63)])
    rulestext = TextAreaField('Rules Text', validators=[Length(max=255)])
    pt_loyalty = StringField('p/t or loyalty', validators=[Length(max=16)])
    
    
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class NewCubeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Create')
