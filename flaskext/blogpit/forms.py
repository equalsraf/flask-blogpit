from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
try:
    from flaskext.wtf import Form, TextField, Required, TextAreaField, Length, HiddenField
except ImportError:
    from flask.ext.wtf import Form, TextField, Required, TextAreaField, Length, HiddenField

from wtforms.validators import StopValidation

class SpamTrap(object):
    """"Field Validator: The field MUST be empty

    If the field is not empty the given message is show

    All fields holding this validator will have a 'is_spamtrap'
    flag set. The following jinja will check for a flag

        {% if form[field_name].flags.is_spamtrap %}

    """
    field_flags = ('is_spamtrap',)

    def __init__(self, message):
        self.message = message
    def __call__(self, form, field):
        if field.data:
            raise StopValidation(self.message)

class SpamTrapField(HiddenField):
    """A spam trap field

    This is a convinience field type to create a Hidden field
    with the SpamTrap validator
    """
    def __init__(self, *args, **kwargs):
        validators=[ SpamTrap('Are you a bot or are you cheating?') ]
        kwargs['validators'] = kwargs.get('validators', validators)
        HiddenField.__init__(self, *args, **kwargs)


class CommentForm(Form):
    name = TextField('name', validators=[Required(), Length(max=100)])
    content = TextAreaField('content', validators=[Required()])

    # Our spam trap fields
    email = SpamTrapField('email')
    trap = SpamTrapField('trap')
