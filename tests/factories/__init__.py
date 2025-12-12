"""
Factory Boy factories for UMIGO tests.

Provides easy creation of test data for all models.
"""
from .users import (
    UserFactory,
    StudentFactory,
    LandlordFactory,
    StaffFactory,
)
from .operations import (
    AdminFactory,
    ReportFactory,
    UserReportFactory,
    ListingReportFactory,
)
from .listings import (
    ZoneFactory,
    ListingFactory,
    ListingPhotoFactory,
    ReviewFactory,
    CommentFactory,
    FavoriteFactory,
)

__all__ = [
    # Users
    'UserFactory',
    'StudentFactory',
    'LandlordFactory',
    'StaffFactory',
    # Operations
    'AdminFactory',
    'ReportFactory',
    'UserReportFactory',
    'ListingReportFactory',
    # Listings
    'ZoneFactory',
    'ListingFactory',
    'ListingPhotoFactory',
    'ReviewFactory',
    'CommentFactory',
    'FavoriteFactory',
]

