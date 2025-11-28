import re

from django.core import validators
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

@deconstructible
class UsernameValidator(validators.RegexValidator):
    regex = r"^[\w ]+\Z"
    message = _(
        "Ingresa un nombre de usuario válido. Solo puede contener letras, espacios y el caracter _"
    )
    flags = 0