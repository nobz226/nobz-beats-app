from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired, Optional

class TrackForm(FlaskForm):
    name = StringField('Track Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    file = FileField('Music File', validators=[DataRequired()])
    artwork = FileField('Primary Artwork', validators=[Optional()])
    artwork_secondary = FileField('Secondary Artwork', validators=[Optional()])
    submit = SubmitField('Upload')