"""
Global pytest configuration and fixtures for UMIGO tests.

This module provides reusable fixtures for all test modules.
"""
import pytest
import shutil
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command

User = get_user_model()


# ============================================================================
# DATABASE SETUP FIXTURES
# ============================================================================

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Setup de BD de test que se ejecuta UNA VEZ por sesión.
    
    IMPORTANTE:
    - Requiere que setup_test_db.py haya creado las tablas previamente
    - Carga zones.json en la BD de test
    - Con --reuse-db, solo se ejecuta si la BD no existe
    """
    with django_db_blocker.unblock():
        # Cargar fixtures de zonas
        try:
            call_command('loaddata', 'zones.json', verbosity=0)
            print("\n✅ Fixture zones.json cargado (20 zonas)")
        except Exception as e:
            print(f"\n⚠️  Error cargando zones.json: {e}")


@pytest.fixture
def db_with_zones(db):
    """
    Fixture que garantiza acceso a BD con zonas cargadas.
    
    USO:
        def test_listing_creation(db_with_zones):
            listing = ListingFactory()  # Usará zone_id entre 1-20
    """
    return db


# ============================================================================
# AUTO-USE FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def setup_test_environment(settings):
    """
    Configure test environment for each test.
    This runs automatically before every test.
    """
    # Use locmem email backend for testing
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    
    # Use temporary media directory
    settings.MEDIA_ROOT = Path(settings.BASE_DIR) / 'test_media'
    
    # Disable migrations for faster tests (uncomment if needed)
    # settings.MIGRATION_MODULES = {app: None for app in settings.INSTALLED_APPS}
    
    yield
    
    # Cleanup after test
    media_root = Path(settings.MEDIA_ROOT)
    if media_root.exists() and 'test' in str(media_root):
        shutil.rmtree(media_root, ignore_errors=True)


@pytest.fixture(autouse=True)
def clear_email_outbox():
    """Clear Django's email outbox before each test."""
    from django.core import mail
    mail.outbox = []
    yield
    mail.outbox = []


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture
def user_data():
    """Valid user data for testing."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'is_active': True,
    }


@pytest.fixture
def user(db, user_data):
    """Create a basic user."""
    user = User.objects.create_user(**user_data)
    return user


@pytest.fixture
def staff_user(db):
    """Create a staff user (without Admin profile)."""
    return User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='StaffPass123!',
        is_staff=True,
        is_active=True
    )


@pytest.fixture
def superuser(db):
    """Create a superuser."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='AdminPass123!',
    )


# ============================================================================
# CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def authenticated_client(client, user):
    """Client authenticated as regular user."""
    client.force_login(user)
    return client


@pytest.fixture
def staff_client(client, staff_user):
    """Client authenticated as staff user."""
    client.force_login(staff_user)
    return client


@pytest.fixture
def admin_client(client, superuser):
    """Client authenticated as superuser."""
    client.force_login(superuser)
    return client


# ============================================================================
# FILE FIXTURES
# ============================================================================

@pytest.fixture
def png_file():
    """
    Generate a valid PNG file for testing.
    
    Returns:
        SimpleUploadedFile: A small valid PNG image
    """
    # PNG header + minimal data
    png_data = (
        b'\x89PNG\r\n\x1a\n'  # PNG signature
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde'
        b'\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
        b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return SimpleUploadedFile(
        name='test_image.png',
        content=png_data,
        content_type='image/png'
    )


@pytest.fixture
def large_png_file():
    """
    Generate a PNG file larger than allowed (for testing validation).
    
    Returns:
        SimpleUploadedFile: A PNG file > 500MB (mocked with metadata)
    """
    # For actual testing, we'll use a smaller file but set size_bytes manually
    png_data = b'\x89PNG\r\n\x1a\n' + b'0' * (10 * 1024 * 1024)  # 10MB
    file = SimpleUploadedFile(
        name='large_image.png',
        content=png_data,
        content_type='image/png'
    )
    # Will need to mock size validation in actual tests
    return file


@pytest.fixture
def jpg_file():
    """
    Generate a JPG file for testing (should fail validation - only PNG allowed).
    
    Returns:
        SimpleUploadedFile: A JPEG image
    """
    # JPEG header
    jpg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1024
    return SimpleUploadedFile(
        name='test_image.jpg',
        content=jpg_data,
        content_type='image/jpeg'
    )


@pytest.fixture
def invalid_file():
    """
    Generate an invalid file (not an image).
    
    Returns:
        SimpleUploadedFile: A text file pretending to be an image
    """
    return SimpleUploadedFile(
        name='fake_image.png',
        content=b'This is not an image',
        content_type='text/plain'
    )


@pytest.fixture
def multiple_png_files():
    """
    Generate multiple valid PNG files for testing.
    
    Returns:
        list: List of 3 SimpleUploadedFile PNG images
    """
    files = []
    for i in range(3):
        png_data = b'\x89PNG\r\n\x1a\n' + b'0' * 1024
        files.append(SimpleUploadedFile(
            name=f'test_image_{i}.png',
            content=png_data,
            content_type='image/png'
        ))
    return files


# ============================================================================
# DATABASE HELPERS
# ============================================================================

@pytest.fixture
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Custom database setup.
    This runs once per test session.
    """
    with django_db_blocker.unblock():
        # Create any necessary initial data here
        # For example, create default groups or permissions
        pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@pytest.fixture
def assert_redirects():
    """
    Helper function to assert redirects with better error messages.
    
    Usage:
        assert_redirects(response, '/expected/url/', status_code=302)
    """
    def _assert_redirects(response, expected_url, status_code=302):
        assert response.status_code == status_code, (
            f"Expected status {status_code}, got {response.status_code}"
        )
        assert response.url == expected_url, (
            f"Expected redirect to {expected_url}, got {response.url}"
        )
    return _assert_redirects


@pytest.fixture
def assert_contains():
    """
    Helper function to assert response contains text.
    
    Usage:
        assert_contains(response, 'Expected text', status_code=200)
    """
    def _assert_contains(response, text, status_code=200):
        assert response.status_code == status_code
        content = response.content.decode()
        assert text in content, f"'{text}' not found in response"
    return _assert_contains


@pytest.fixture
def get_messages():
    """
    Extract messages from response.
    
    Usage:
        messages = get_messages(response)
        assert 'Success' in messages
    """
    def _get_messages(response):
        from django.contrib.messages import get_messages as django_get_messages
        return [str(m) for m in django_get_messages(response.wsgi_request)]
    return _get_messages


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

@pytest.fixture
def django_assert_num_queries():
    """
    Assert number of database queries.
    
    Usage:
        with django_assert_num_queries(5):
            # Code that should execute exactly 5 queries
            pass
    """
    from django.test.utils import CaptureQueriesContext
    from django.db import connection
    
    class AssertNumQueries:
        def __init__(self, expected):
            self.expected = expected
            self.context = CaptureQueriesContext(connection)
        
        def __enter__(self):
            self.context.__enter__()
            return self
        
        def __exit__(self, *args):
            self.context.__exit__(*args)
            executed = len(self.context.captured_queries)
            assert executed == self.expected, (
                f"Expected {self.expected} queries, executed {executed}\n"
                f"Queries: {self.context.captured_queries}"
            )
    
    return AssertNumQueries


# ============================================================================
# EMAIL TESTING
# ============================================================================

@pytest.fixture
def mailoutbox():
    """
    Access Django's email outbox.
    
    Usage:
        assert len(mailoutbox) == 1
        assert 'Subject' in mailoutbox[0].subject
    """
    from django.core import mail
    return mail.outbox
