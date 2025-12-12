"""
Factory Boy factories for operations models.

Creates test instances of Admin, Report, UserReport, ListingReport.
"""
import factory
from factory.django import DjangoModelFactory
from operations.models import Admin
from inquiries.models import Report, UserReport, ListingReport
from .users import StaffFactory, UserFactory


class AdminFactory(DjangoModelFactory):
    """
    Factory for Admin model (with OneToOne User).
    
    The user must be staff to have an Admin profile.
    
    Usage:
        admin = AdminFactory()
        admin = AdminFactory(user__username='moderator')
        admin = AdminFactory(user=existing_staff_user)
    """
    class Meta:
        model = Admin
    
    user = factory.SubFactory(StaffFactory)


class ReportFactory(DjangoModelFactory):
    """
    Factory for Report model (base).
    
    IMPORTANTE: NO crear Report directamente, usar UserReportFactory o ListingReportFactory.
    
    Usage:
        # Para reportar usuario:
        user_report = UserReportFactory(reported_user=user)
        
        # Para reportar listing:
        listing_report = ListingReportFactory(listing=listing)
    """
    class Meta:
        model = Report
    
    reporter = factory.SubFactory(UserFactory)
    reason = factory.Faker('sentence')
    status = 'UNDER_REVIEW'
    reviewed_by = None
    reviewed_at = None


class UserReportFactory(DjangoModelFactory):
    """
    Factory for UserReport model (reporte contra un usuario).
    
    Usage:
        user_report = UserReportFactory(reported_user=target_user)
        user_report = UserReportFactory(
            report__reporter=reporter_user,
            reported_user=target_user
        )
    """
    class Meta:
        model = UserReport
    
    report = factory.SubFactory(ReportFactory)
    reported_user = factory.SubFactory(UserFactory)


class ListingReportFactory(DjangoModelFactory):
    """
    Factory for ListingReport model (reporte contra un listing).
    
    Usage:
        listing_report = ListingReportFactory(listing=listing)
        listing_report = ListingReportFactory(
            report__reporter=reporter_user,
            listing=listing
        )
    """
    class Meta:
        model = ListingReport
    
    report = factory.SubFactory(ReportFactory)
    
    @factory.lazy_attribute
    def listing(self):
        # Import here to avoid circular dependency
        from .listings import ListingFactory
        return ListingFactory()

