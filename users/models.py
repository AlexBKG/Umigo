from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

from .validators import UsernameValidator

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

    class Meta:
        managed = False
        db_table = 'users_user'

    def __str__(self):
        return self.username
    
class Student(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'student_profile')

    class Meta:
        managed = False
        db_table = 'users_student'
    
    def clean(self):
        """
        Validación: Un usuario no puede ser Student y Landlord simultáneamente.
        """
        super().clean()
        if hasattr(self.user, 'landlord_profile'):
            raise ValidationError(
                'Este usuario ya es un Landlord. Un usuario no puede ser Student y Landlord al mismo tiempo.'
            )

    def receiveAvailabilityNotification(self, domain, listing):
        mail_subject = 'Umigo: ¡Uno de tus arriendos favoritos está disponible!'
        message = render_to_string('users/favoriteListingAvailableEmail.html', {
            'user': self.user,
            'domain': domain,
            'listing': listing.pk
        })
        to_email = self.user.email
        email = EmailMessage(
            mail_subject, message, to=[to_email]
        )
        email.send()

    def __str__(self):
        return self.user.username
    
class Landlord(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='landlord_profile')
    national_id = models.CharField(max_length=20)
    id_url = models.FileField(upload_to='identificationCards')

    class Meta:
        managed = False
        db_table = 'users_landlord'
    
    def clean(self):
        """
        Validación: Un usuario no puede ser Landlord y Student simultáneamente.
        """
        super().clean()
        if hasattr(self.user, 'student_profile'):
            raise ValidationError(
                'Este usuario ya es un Student. Un usuario no puede ser Landlord y Student al mismo tiempo.'
            )

    def __str__(self):
        return self.user.username