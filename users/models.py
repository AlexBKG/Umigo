from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import UsernameValidator

class Report(models.Model):
    pass

class User(AbstractUser):
    username_validator = UsernameValidator()

    username = models.CharField(
        "username",
        max_length=150,
        unique=True,
        help_text= "Requerido. 150 caracteres o menos. Solo letras, espacios y el caracter _",
        validators=[username_validator],
        error_messages={
            "unique": "Ya existe un usuario con ese nombre.",
        },
    )
    

    email = models.EmailField("Dirección de correo", blank=False, unique=True, error_messages={"unique": "Ya existe una cuenta registrada con ese correo.",})
    suspension_end_at = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.username
    
class Student(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'student_profile')

    def __str__(self):
        return self.user.username
    
class Landlord(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='landlord_profile')
    national_id = models.CharField(max_length=20)
    id_url = models.FileField(upload_to='identificationCards')

    def __str__(self):
        return self.user.username