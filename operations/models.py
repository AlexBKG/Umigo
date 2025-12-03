from django.db import models


class Admin(models.Model):
    """
    Administrador del sistema.
    Tabla independiente sin relación directa con User.
    Solo se relaciona con Report a través de reviewed_by.
    """
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin'
        managed = False

    def __str__(self):
        return f"Admin #{self.id}"
