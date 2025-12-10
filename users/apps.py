from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    
    def ready(self):
        """
        Importa signals cuando la app se inicializa.
        
        Este método se ejecuta una vez cuando Django arranca,
        registrando todos los signals definidos en users/signals.py
        """
        import users.signals  # noqa: F401
