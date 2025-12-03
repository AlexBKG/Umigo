from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from users.models import User
from operations.models import Admin
from listings.models import Listing


class Report(models.Model):
    """Sistema de reportes para usuarios y listings (XOR: usuario O listing)"""
    STATUS_CHOICES = [
        ('UNDER_REVIEW', 'En Revisión'),
        ('ACCEPTED', 'Aceptado'),
        ('REJECTED', 'Rechazado'),
    ]

    id = models.BigAutoField(primary_key=True)
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_made'
    )
    reason = models.CharField(max_length=255)
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default='UNDER_REVIEW'
    )
    reviewed_by = models.ForeignKey(
        Admin,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='reviewed_by',
        help_text='Administrador que revisó el reporte'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'report'
        managed = False
        indexes = [
            models.Index(fields=['reporter'], name='ix_report_reporter'),
            models.Index(fields=['status'], name='ix_report_status'),
            models.Index(fields=['reviewed_by'], name='ix_report_reviewer'),
        ]

    def __str__(self):
        return f"Reporte #{self.id} - {self.status}"

    @property
    def target_user(self):
        try:
            return self.userreport.reported_user
        except UserReport.DoesNotExist:
            return None

    @property
    def target_listing(self):
        try:
            return self.listingreport.listing
        except ListingReport.DoesNotExist:
            return None

    @property
    def target_type(self):
        if hasattr(self, 'userreport'):
            return 'USER'
        elif hasattr(self, 'listingreport'):
            return 'LISTING'
        return None

    def clean(self):
        if self.status != 'UNDER_REVIEW' and not self.reviewed_by:
            raise ValidationError(
                "Los reportes aceptados o rechazados deben tener un administrador asignado"
            )

    def _apply_user_moderation_on_accept(self):
        """
        Implementa la lógica del trigger de moderación (emula trg_report_moderation_on_accept_corrected):
        - 1er reporte aceptado: suspender 30 días
        - 2+ reportes aceptados: eliminar cuenta
        
        Solo aplica si el target es USER.
        """
        if not hasattr(self, 'userreport'):
            return  # Solo aplica a reportes contra usuarios

        reported_user = self.userreport.reported_user
        accepted_count = UserReport.objects.filter(
            reported_user=reported_user,
            report__status='ACCEPTED'
        ).count()

        if accepted_count == 1:
            # Primera infracción: suspender por 30 días
            reported_user.is_active = False
            reported_user.suspension_end_at = timezone.now().date() + timezone.timedelta(days=30)
            reported_user.save(update_fields=['is_active', 'suspension_end_at'])
        elif accepted_count >= 2:
            # Segunda+ infracción: eliminar cuenta
            reported_user.delete()

    def save(self, *args, **kwargs):
        # Detectar transición de estado (emula AFTER UPDATE ON report)
        old_status = None
        if self.pk:
            try:
                old_status = Report.objects.filter(pk=self.pk).values_list('status', flat=True).first()
            except Report.DoesNotExist:
                pass

        # Auto-establecer reviewed_at cuando se cambia el status (emula trigger trg_report_review_validation)
        if self.status != 'UNDER_REVIEW' and self.reviewed_by and not self.reviewed_at:
            self.reviewed_at = timezone.now()
        
        self.clean()
        super().save(*args, **kwargs)

        # Si pasó a ACCEPTED y antes no lo estaba, aplicar moderación (si target es USER)
        if old_status in (None, 'UNDER_REVIEW', 'REJECTED') and self.status == 'ACCEPTED':
            self._apply_user_moderation_on_accept()


class ListingReport(models.Model):
    """Reporte específico contra un listing"""
    report = models.OneToOneField(
        Report,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='listingreport'
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='reports'
    )

    class Meta:
        db_table = 'listing_report'
        managed = False
        indexes = [
            models.Index(fields=['listing'], name='ix_lreport_listing'),
        ]

    def __str__(self):
        return f"Reporte Listing: #{self.report_id} -> Listing #{self.listing_id}"

    def clean(self):
        if UserReport.objects.filter(report_id=self.report_id).exists():
            raise ValidationError(
                "El reporte ya apunta a un usuario; no puede apuntar también a un listing"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class UserReport(models.Model):
    """Reporte específico contra un usuario"""
    report = models.OneToOneField(
        Report,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='userreport'
    )
    reported_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_received'
    )

    class Meta:
        db_table = 'user_report'
        managed = False
        indexes = [
            models.Index(fields=['reported_user'], name='ix_ureport_user'),
        ]

    def __str__(self):
        return f"Reporte Usuario: #{self.report_id} -> {self.reported_user.email}"

    def clean(self):
        if ListingReport.objects.filter(report_id=self.report_id).exists():
            raise ValidationError(
                "El reporte ya apunta a un listing; no puede apuntar también a un usuario"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        # Si ya está ACCEPTED en el momento de crear el vínculo, aplicar moderación
        if self.report.status == 'ACCEPTED':
            self.report._apply_user_moderation_on_accept()


"""
Servicio para crear reportes (stored procedure sp_create_report).
Comentado - ajustar según necesidad.

from django.db import transaction

@transaction.atomic
def create_report(reporter_id, reason, target_kind, target_id):
    '''
    Crea un reporte de forma atómica (equivalente al stored procedure).
    
    Args:
        reporter_id (int): ID del usuario que hace el reporte
        reason (str): Motivo del reporte
        target_kind (str): 'USER' o 'LISTING'
        target_id (int): ID del objetivo (user_id o listing_id)
    
    Returns:
        Report: Instancia del reporte creado
    
    Raises:
        ValidationError: Si los datos son inválidos
    '''
    target_kind = (target_kind or "").upper()
    
    if target_kind not in ('USER', 'LISTING'):
        raise ValidationError("target_kind debe ser 'USER' o 'LISTING'")
    
    # Validar existencia del target
    if target_kind == 'USER':
        if not User.objects.filter(pk=target_id).exists():
            raise ValidationError("El usuario objetivo no existe")
    else:
        if not Listing.objects.filter(pk=target_id).exists():
            raise ValidationError("El listing objetivo no existe")
    
    # Crear el reporte
    report = Report.objects.create(
        reporter_id=reporter_id,
        reason=reason
    )
    
    # Crear el registro específico (USER o LISTING)
    if target_kind == 'USER':
        UserReport.objects.create(
            report=report,
            reported_user_id=target_id
        )
    else:
        ListingReport.objects.create(
            report=report,
            listing_id=target_id
        )
    
    return report

"""
