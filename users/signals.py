"""
Signals para el módulo de usuarios.

Este módulo contiene signals que se ejecutan automáticamente
cuando ocurren ciertos eventos en los modelos de usuarios.
"""
from django.db.models.signals import pre_save
from django.dispatch import receiver

from users.models import User, Landlord


@receiver(pre_save, sender=User)
def deactivate_landlord_listings_on_user_deactivate(sender, instance: User, **kwargs):
    """
    Oculta todos los listings de un landlord cuando su usuario se desactiva.
    
    COMPORTAMIENTO:
    - Cuando un User pasa de is_active=True → is_active=False
    - Si ese User tiene perfil de Landlord
    - Entonces marca todos sus listings como available=False
    
    RAZÓN:
    - No tiene sentido mostrar arriendos de usuarios suspendidos/inactivos
    - Evita inquiries/contactos a usuarios que no pueden responder
    - Mejora la experiencia de usuario (no publicaciones "fantasma")
    
    NOTA IMPORTANTE:
    - Al reactivar al usuario (is_active False→True), los listings NO se reactivan
      automáticamente. El landlord debe revisarlos y activarlos manualmente.
    - Esto es por seguridad: evita publicar listings desactualizados (fotos viejas,
      precio incorrecto, etc.)
    
    CASOS DE USO:
    1. Auto-moderación: Trigger acepta reporte → desactiva user → este signal oculta listings
    2. Admin manual: Admin desactiva user en Django admin → este signal oculta listings
    3. Cualquier otra vía que haga user.save() con is_active=False
    
    COMPLEMENTARIO CON TRIGGER MYSQL:
    - Este signal funciona en dev/SQLite y producción/MySQL
    - El Trigger 12 en MySQL hace lo mismo (redundancia es buena aquí)
    - Si ambos se ejecutan, es idempotente (ambos ponen available=False)
    
    Args:
        sender: La clase del modelo (User)
        instance: La instancia del User siendo guardada
        **kwargs: Argumentos adicionales del signal
    """
    # Si es usuario nuevo (no tiene pk), no aplica
    if not instance.pk:
        return
    
    # Obtener el estado anterior del usuario desde la BD
    try:
        old_user = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        # Usuario no existe aún en BD (caso raro pero posible)
        return
    
    # Detectar transición: activo → inactivo
    if old_user.is_active and not instance.is_active:
        # Verificar si este usuario tiene perfil de Landlord
        try:
            landlord = Landlord.objects.get(user=instance)
        except Landlord.DoesNotExist:
            # No es landlord, no hacer nada
            return
        
        # Importar aquí para evitar circular imports
        from listings.models import Listing
        
        # Marcar como NO disponibles todos los listings activos de este landlord
        updated_count = Listing.objects.filter(
            owner=landlord,
            available=True
        ).update(available=False)
        
        # Log para debugging (opcional, puedes comentarlo en producción)
        if updated_count > 0:
            print(f"[SIGNAL] Ocultados {updated_count} listings del landlord {landlord.user.username} (user_id={instance.pk})")
