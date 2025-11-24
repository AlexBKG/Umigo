from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_suspended = models.BooleanField(default=False)
    suspension_end_at = models.DateTimeField(null=True, blank=True)

    # username y password ya vienen de AbstractUser

    def __str__(self):
        return self.username


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Student: {self.user.username}"


class Landlord(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='landlord_profile'
    )
    national_id = models.CharField(max_length=20)
    id_front_url = models.URLField(max_length=300)
    id_back_url = models.URLField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Landlord: {self.user.username}"
