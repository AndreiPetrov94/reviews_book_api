import re

from django.core.exceptions import ValidationError


def validation_username(value):
    if not bool(re.match(r'^[\w.@+-]+\Z', value)):
        raise ValidationError(
            'Недопустимые символы в никнейме'
        )
    return value
