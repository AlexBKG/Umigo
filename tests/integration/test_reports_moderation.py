# tests/integration/test_reports_moderation.py
"""
Tests para Reportes y Sistema de Moderación (8 tests)
PRIORIDAD: CRÍTICA
TIEMPO ESTIMADO: 4 horas
DÍA: Martes (9:00-13:00)

IMPORTANTE: Estos son tests de INTEGRACIÓN porque prueban:
- Lógica de negocio compleja (moderación automática)
- Transiciones de estado en Report
- Side effects (suspensión, eliminación de usuarios)
"""

import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from tests.factories import (
    UserFactory,
    AdminFactory,
    ListingFactory,
    UserReportFactory,
    ListingReportFactory,
)
from inquiries.models import Report, UserReport, ListingReport

User = get_user_model()


@pytest.mark.django_db
class TestReportCreation:
    """Tests para creación de reportes (XOR: User O Listing)"""

    def test_create_user_report(self):
        """✅ Crear reporte contra un usuario"""
        reporter = UserFactory()
        target_user = UserFactory()
        
        # Usar factory que crea Report + UserReport automáticamente
        user_report = UserReportFactory(
            report__reporter=reporter,
            reported_user=target_user,
            report__reason="Comportamiento inapropiado"
        )
        
        assert user_report.report.status == 'UNDER_REVIEW'
        assert user_report.reported_user == target_user
        assert user_report.report.target_user == target_user  # Property

    def test_create_listing_report(self):
        """✅ Crear reporte contra un listing"""
        reporter = UserFactory()
        listing = ListingFactory()
        
        # Usar factory que crea Report + ListingReport automáticamente
        listing_report = ListingReportFactory(
            report__reporter=reporter,
            listing=listing,
            report__reason="Información falsa"
        )
        
        assert listing_report.listing == listing
        assert listing_report.report.target_listing == listing  # Property

    def test_report_xor_constraint(self):
        """✅ Reporte solo puede apuntar a usuario O listing (XOR)"""
        reporter = UserFactory()
        target_user = UserFactory()
        listing = ListingFactory()
        
        # Crear UserReport primero
        user_report = UserReportFactory(
            report__reporter=reporter,
            reported_user=target_user,
            report__reason="Test XOR"
        )
        
        # Intentar crear ListingReport con el MISMO report (debe fallar)
        with pytest.raises(ValidationError):
            listing_report = ListingReport(report=user_report.report, listing=listing)
            listing_report.clean()  # Trigger validación XOR


@pytest.mark.django_db
class TestReportStatusChanges:
    """Tests para cambios de estado del reporte"""

    def test_report_status_change_accepted(self):
        """✅ Cambiar status de UNDER_REVIEW a ACCEPTED"""
        admin = AdminFactory()
        user_report = UserReportFactory(report__status='UNDER_REVIEW')
        
        # Cambiar estado
        report = user_report.report
        report.status = 'ACCEPTED'
        report.reviewed_by = admin
        report.save()
        
        report.refresh_from_db()
        assert report.status == 'ACCEPTED'
        assert report.reviewed_by == admin
        assert report.reviewed_at is not None

    def test_report_status_change_rejected(self):
        """✅ Cambiar status de UNDER_REVIEW to REJECTED"""
        admin = AdminFactory()
        user_report = UserReportFactory(report__status='UNDER_REVIEW')
        
        # Cambiar estado
        report = user_report.report
        report.status = 'REJECTED'
        report.reviewed_by = admin
        report.save()
        
        report.refresh_from_db()
        assert report.status == 'REJECTED'
        assert report.reviewed_by == admin

    def test_report_must_have_reviewer_when_not_under_review(self):
        """✅ Reportes ACCEPTED/REJECTED deben tener reviewed_by"""
        user_report = UserReportFactory(report__status='UNDER_REVIEW')
        
        # Intentar cambiar a ACCEPTED sin reviewed_by (debe fallar)
        report = user_report.report
        report.status = 'ACCEPTED'
        report.reviewed_by = None
        
        with pytest.raises(ValidationError):
            report.save()  # Report.clean() valida esto


@pytest.mark.django_db
class TestUserModeration:
    """Tests para sistema de moderación automática de usuarios"""

    def test_user_moderation_first_accepted_suspends_30_days(self):
        """✅ 1er reporte aceptado → suspender usuario por 30 días"""
        target_user = UserFactory(is_active=True)
        admin = AdminFactory()
        
        # Crear reporte contra usuario
        user_report = UserReportFactory(
            report__reporter=UserFactory(),
            reported_user=target_user,
            report__reason="Fraude"
        )
        
        # Aceptar reporte (trigger moderación)
        report = user_report.report
        report.status = 'ACCEPTED'
        report.reviewed_by = admin
        report.save()
        
        # Verificar suspensión
        target_user.refresh_from_db()
        assert target_user.is_active == False
        assert target_user.suspension_end_at is not None
        
        # Verificar que la suspensión es ~30 días
        days_suspended = (target_user.suspension_end_at - date.today()).days
        assert days_suspended in [29, 30, 31]  # Tolerancia ±1 día

    def test_user_moderation_second_accepted_deletes_user(self):
        """✅ 2º reporte aceptado → eliminar usuario permanentemente"""
        target_user = UserFactory(is_active=True)
        admin = AdminFactory()
        user_pk = target_user.pk
        
        # ====== 1ER REPORTE ACEPTADO ======
        user_report1 = UserReportFactory(
            report__reporter=UserFactory(),
            reported_user=target_user,
            report__reason="Infracción #1"
        )
        
        report1 = user_report1.report
        report1.status = 'ACCEPTED'
        report1.reviewed_by = admin
        report1.save()
        
        # Verificar que fue suspendido (no eliminado)
        target_user.refresh_from_db()
        assert target_user.is_active == False
        
        # ====== 2º REPORTE ACEPTADO ======
        user_report2 = UserReportFactory(
            report__reporter=UserFactory(),
            reported_user=target_user,
            report__reason="Infracción #2"
        )
        
        report2 = user_report2.report
        report2.status = 'ACCEPTED'
        report2.reviewed_by = admin
        report2.save()
        
        # Verificar que el usuario fue ELIMINADO
        with pytest.raises(User.DoesNotExist):
            User.objects.get(pk=user_pk)
