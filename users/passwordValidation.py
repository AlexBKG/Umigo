import re
from django.core.exceptions import (
    ValidationError,
)

from django.contrib.auth.password_validation import *

class LengthValidator:
    def __init__(self, min_length=8, max_length=44):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                self.get_error_message(),
                code="password_too_short",
                params={"min_length": self.min_length},
            )
        elif len(password) > self.max_length:
            raise ValidationError(
                self.get_error_message(),
                code="password_too_long",
                params={"max_length": self.max_length},
            )

    def get_error_message(self):
        return "La contraseña debe tener entre " + str(self.min_length) + " y " + str(self.max_length) + " caracteres de longitud."

    def get_help_text(self):
        return "Tu contraseña debe tener entre " + str(self.min_length) + " y " + str(self.max_length) + " caracteres de longitud."
    
class CustomUserAttributeSimilarityValidator(UserAttributeSimilarityValidator):
    def get_error_message(self):
        return "La contraseña es muy similar a otro de los campos que ingresaste."

    def get_help_text(self):
        return "Tu contraseña no puede ser muy similar al resto de información que ingresas."
    

class CustomUserCommonPasswordValidator(CommonPasswordValidator):
    def get_error_message(self):
        return "La contraseña escogida es muy común."

    def get_help_text(self):
        return "Tu contraseña no puede ser una contraseña comúnmente utilizada."
    
class CharacterTypesValidator:
    def validate(self, password, user=None):
        if re.search("^([^0-9]*|[^A-Z]*|[^a-z]*|[a-zA-Z0-9]*)$", password):
            raise ValidationError(
                self.get_error_message(),
                code="password_not_alphanumeric_and_special_char",
            )

    def get_error_message(self):
        return "Tu contraseña no contiene números o caracteres especiales o no contiene letras minúsculas o mayúsculas"

    def get_help_text(self):
        return "Tu contraseña debe contener por lo menos un número, un caracter especial, una letra minúscula y una mayúscula"