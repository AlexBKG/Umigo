"""
Service layer for report creation with business logic.
Provides transaction-safe report creation with deduplication and validation.
"""
from datetime import timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Report, UserReport, ListingReport
from users.models import User
from listings.models import Listing


class ReportService:
    """
    Service class for handling report creation and validation.
    Implements business rules including 24h cooldown period per target.
    """
    
    # Cooldown period (24 hours)
    COOLDOWN_HOURS = 24
    
    @classmethod
    def _check_duplicate_report(cls, reporter, target_type, target_id):
        """
        Check if reporter has already reported this target in the last 24 hours.
        
        Args:
            reporter (User): User making the report
            target_type (str): 'USER' or 'LISTING'
            target_id (int): ID of the target
            
        Raises:
            ValidationError: If duplicate report found within cooldown period
        """
        cooldown_threshold = timezone.now() - timedelta(hours=cls.COOLDOWN_HOURS)
        
        # Build query based on target type
        if target_type == 'USER':
            recent_report = Report.objects.filter(
                reporter=reporter,
                created_at__gte=cooldown_threshold,
                userreport__reported_user_id=target_id
            ).first()
        elif target_type == 'LISTING':
            recent_report = Report.objects.filter(
                reporter=reporter,
                created_at__gte=cooldown_threshold,
                listingreport__listing_id=target_id
            ).first()
        else:
            return  # Invalid target_type, will be caught by other validation
        
        if recent_report:
            # Calculate time remaining
            time_since = timezone.now() - recent_report.created_at
            hours_passed = int(time_since.total_seconds() / 3600)
            hours_left = cls.COOLDOWN_HOURS - hours_passed
            
            target_name = 'usuario' if target_type == 'USER' else 'publicación'
            
            raise ValidationError(
                f"Ya reportaste a este {target_name} hace {hours_passed} hora(s). "
                f"Debes esperar {hours_left} hora(s) más para reportar nuevamente."
            )
    
    @classmethod
    def _validate_target_exists(cls, target_type, target_id):
        """
        Validate that the target (User or Listing) exists in the database.
        
        Args:
            target_type (str): 'USER' or 'LISTING'
            target_id (int): ID of the target
            
        Returns:
            User or Listing: The target object
            
        Raises:
            ValidationError: If target doesn't exist
        """
        if target_type == 'USER':
            try:
                return User.objects.get(pk=target_id)
            except User.DoesNotExist:
                raise ValidationError("El usuario reportado no existe")
        
        elif target_type == 'LISTING':
            try:
                return Listing.objects.get(pk=target_id)
            except Listing.DoesNotExist:
                raise ValidationError("La publicación reportada no existe")
        
        else:
            raise ValidationError(
                "Tipo de objetivo inválido. Debe ser 'USER' o 'LISTING'"
            )
    
    @classmethod
    def _validate_business_rules(cls, reporter, target_type, target_obj):
        """
        Validate business rules for reporting.
        
        Args:
            reporter (User): User making the report
            target_type (str): 'USER' or 'LISTING'
            target_obj (User or Listing): The target object
            
        Raises:
            ValidationError: If business rules are violated
        """
        if target_type == 'USER':
            # Cannot report yourself
            if target_obj == reporter:
                raise ValidationError("No puedes reportarte a ti mismo")
            
            # Cannot report administrators
            if target_obj.is_staff or target_obj.is_superuser:
                raise ValidationError("No se pueden reportar administradores")
        
        elif target_type == 'LISTING':
            # Only students can report listings
            if reporter.user_type != 'STUDENT':
                raise ValidationError(
                    "Solo los estudiantes pueden reportar publicaciones"
                )
            
            # Cannot report your own listing (if reporter is landlord)
            if hasattr(reporter, 'landlord') and target_obj.landlord == reporter.landlord:
                raise ValidationError("No puedes reportar tu propia publicación")
    
    @classmethod
    @transaction.atomic
    def create_report(cls, reporter, reason, target_type, target_id):
        """
        Create a report with full validation and transaction safety.
        
        This is the main entry point for creating reports. It performs:
        1. Input validation
        2. Target existence check
        3. Deduplication check (24h cooldown)
        4. Business rules validation
        5. Atomic report creation (Report + UserReport/ListingReport)
        
        Args:
            reporter (User): User creating the report
            reason (str): Reason for the report (max 255 chars)
            target_type (str): 'USER' or 'LISTING'
            target_id (int): ID of the reported user or listing
            
        Returns:
            Report: The created report instance
            
        Raises:
            ValidationError: If any validation fails
            
        Example:
            report = ReportService.create_report(
                reporter=request.user,
                reason="Contenido fraudulento en la publicación",
                target_type='LISTING',
                target_id=123
            )
        """
        # Normalize target_type
        target_type = (target_type or "").upper()
        
        # Validate inputs
        if not reporter:
            raise ValidationError("No se ha especificado el usuario que reporta")
        
        if not reason or not reason.strip():
            raise ValidationError("El motivo del reporte es obligatorio")
        
        reason = reason.strip()
        if len(reason) < 10:
            raise ValidationError(
                "El motivo del reporte debe tener al menos 10 caracteres"
            )
        
        if len(reason) > 255:
            raise ValidationError(
                "El motivo del reporte no puede exceder 255 caracteres"
            )
        
        if target_type not in ('USER', 'LISTING'):
            raise ValidationError(
                "Tipo de objetivo inválido. Debe ser 'USER' o 'LISTING'"
            )
        
        if not target_id:
            raise ValidationError("No se ha especificado el objetivo del reporte")
        
        # Check for duplicate reports (24h cooldown)
        cls._check_duplicate_report(reporter, target_type, target_id)
        
        # Validate target exists
        target_obj = cls._validate_target_exists(target_type, target_id)
        
        # Validate business rules
        cls._validate_business_rules(reporter, target_type, target_obj)
        
        # Create the report (atomic transaction)
        report = Report.objects.create(
            reporter=reporter,
            reason=reason
        )
        
        # Create the specific report type (XOR: User OR Listing)
        if target_type == 'USER':
            UserReport.objects.create(
                report=report,
                reported_user=target_obj
            )
        else:  # LISTING
            ListingReport.objects.create(
                report=report,
                listing=target_obj
            )
        
        return report
    
    @classmethod
    def get_recent_reports_count(cls, reporter, target_type=None):
        """
        Get count of reports made by a user in the last 24 hours.
        Useful for rate limiting or analytics.
        
        Args:
            reporter (User): User to check
            target_type (str, optional): Filter by 'USER' or 'LISTING'
            
        Returns:
            int: Number of reports in last 24 hours
        """
        cooldown_threshold = timezone.now() - timedelta(hours=cls.COOLDOWN_HOURS)
        
        queryset = Report.objects.filter(
            reporter=reporter,
            created_at__gte=cooldown_threshold
        )
        
        if target_type == 'USER':
            queryset = queryset.filter(userreport__isnull=False)
        elif target_type == 'LISTING':
            queryset = queryset.filter(listingreport__isnull=False)
        
        return queryset.count()
    
    @classmethod
    def can_report_target(cls, reporter, target_type, target_id):
        """
        Check if a user can report a specific target (respecting cooldown).
        Returns (can_report: bool, reason: str)
        
        Args:
            reporter (User): User wanting to report
            target_type (str): 'USER' or 'LISTING'
            target_id (int): ID of the target
            
        Returns:
            tuple: (bool, str) - (can_report, reason_if_cannot)
        """
        try:
            cls._check_duplicate_report(reporter, target_type, target_id)
            target_obj = cls._validate_target_exists(target_type, target_id)
            cls._validate_business_rules(reporter, target_type, target_obj)
            return (True, "")
        except ValidationError as e:
            return (False, str(e))
