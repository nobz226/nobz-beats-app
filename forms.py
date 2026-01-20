from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Optional, Length, EqualTo, ValidationError
from models import User

class TrackForm(FlaskForm):
    name = StringField('Track Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    file = FileField('Music File', validators=[DataRequired()])
    artwork = FileField('Primary Artwork', validators=[Optional()])
    artwork_secondary = FileField('Secondary Artwork', validators=[Optional()])
    submit = SubmitField('Upload')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=150, message='Username must be between 3 and 150 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')


class PlaylistForm(FlaskForm):
    name = StringField('Playlist Name', validators=[
        DataRequired(),
        Length(min=1, max=200, message='Playlist name must be between 1 and 200 characters')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Create Playlist')