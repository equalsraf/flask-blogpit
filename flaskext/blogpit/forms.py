from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
from flaskext.wtf import Form, TextField, Required, TextAreaField

class CommentForm(Form):
    name = TextField('name', validators=[Required()])
    content = TextAreaField('content', validators=[Required()])


