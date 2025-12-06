from django.db import models
from django.conf import settings


class Admin(models.Model):
    """
    Administrador del sistema.
    Vinculado con User de Django para identificar quién revisó reportes.
    """
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='admin_profile',
        help_text='Usuario Django asociado a este administrador'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin'
        managed = False

    def __str__(self):
        if self.user:
            return f"Admin: {self.user.username}"
        return f"Admin #{self.id}"
