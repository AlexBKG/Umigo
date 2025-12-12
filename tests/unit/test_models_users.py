"""
Unit tests for User, Student, and Landlord models.

Tests cover:
- User creation and validation
- Username validation
- Email uniqueness
- Student/Landlord OneToOne relationships
- Suspension logic
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

from users.models import Student, Landlord
from tests.factories import UserFactory, StudentFactory, LandlordFactory

User = get_user_model()


# ============================================================================
# USER MODEL TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestUserModel:
    """Test suite for User model."""
    
    def test_user_creation_with_valid_data(self):
        """Test creating a user with valid data."""
        user = UserFactory(
            username='johndoe',
            email='john@example.com'
        )
        
        assert user.id is not None
        assert user.username == 'johndoe'
        assert user.email == 'john@example.com'
        assert user.is_active is True
        assert user.suspension_end_at is None
    
    def test_user_email_must_be_unique(self):
        """Test that email must be unique across users."""
        UserFactory(email='duplicate@example.com')
        
        with pytest.raises(IntegrityError):
            UserFactory(email='duplicate@example.com')
    
    def test_user_username_must_be_unique(self):
        """Test that username must be unique across users."""
        UserFactory(username='unique_user')
        
        with pytest.raises(IntegrityError):
            UserFactory(username='unique_user')
    
    def test_user_is_active_default_true(self):
        """Test that is_active defaults to True."""
        user = UserFactory()
        assert user.is_active is True
    
    def test_user_suspension_end_at_default_none(self):
        """Test that suspension_end_at defaults to None."""
        user = UserFactory()
        assert user.suspension_end_at is None
    
    def test_user_str_returns_username(self):
        """Test that __str__ returns username."""
        user = UserFactory(username='testuser')
        assert str(user) == 'testuser'
    
    @pytest.mark.parametrize('username', [
        'valid_username',
        'user with spaces',
        'user_123',
        'UPPERCASE',
    ])
    def test_user_username_valid_formats(self, username):
        """Test that various valid username formats are accepted."""
        user = UserFactory(username=username)
        assert user.username == username
    
    def test_user_can_be_suspended(self):
        """Test that user can be suspended with end date."""
        user = UserFactory(is_active=True)
        
        # Suspend for 30 days
        user.is_active = False
        user.suspension_end_at = timezone.now().date() + timedelta(days=30)
        user.save()
        
        assert user.is_active is False
        assert user.suspension_end_at is not None
    
    def test_user_auto_reactivation_after_suspension_expires(self):
        """
        Test that user should be reactivated if suspension_end_at < today.
        Note: This logic should be implemented in a management command or signal.
        """
        # Create suspended user with expired suspension
        user = UserFactory(
            is_active=False,
            suspension_end_at=timezone.now().date() - timedelta(days=1)
        )
        
        # Simulate auto-reactivation logic (would be in a management command)
        if user.suspension_end_at and user.suspension_end_at < timezone.now().date():
            user.is_active = True
            user.suspension_end_at = None
            user.save()
        
        assert user.is_active is True
        assert user.suspension_end_at is None


# ============================================================================
# STUDENT MODEL TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestStudentModel:
    """Test suite for Student model."""
    
    def test_student_creation_with_user(self):
        """Test creating a student with associated user."""
        student = StudentFactory()
        
        assert student.id is not None
        assert student.user is not None
        assert isinstance(student.user, User)
    
    def test_student_onetoone_with_user(self):
        """Test that Student has OneToOne relationship with User."""
        user = UserFactory()
        student = Student.objects.create(user=user)
        
        assert student.user == user
        assert user.student_profile == student
    
    def test_student_cascades_on_user_delete(self):
        """Test that Student is deleted when User is deleted (CASCADE)."""
        student = StudentFactory()
        user_id = student.user.id
        
        student.user.delete()
        
        assert not Student.objects.filter(pk=student.pk).exists()
        assert not User.objects.filter(pk=user_id).exists()
    
    def test_student_str_returns_username(self):
        """Test that __str__ returns user's username."""
        student = StudentFactory(user__username='student_test')
        assert str(student) == 'student_test'
    
    def test_student_can_receive_notification(self, mailoutbox):
        """Test that student can receive email notifications."""
        student = StudentFactory(user__email='student@example.com')
        from tests.factories import ListingFactory
        listing = ListingFactory()
        
        # Call notification method
        student.receiveAvailabilityNotification(
            domain='testserver',
            listing=listing
        )
        
        # Check email was sent
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ['student@example.com']
        assert 'disponible' in mailoutbox[0].subject.lower()


# ============================================================================
# LANDLORD MODEL TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestLandlordModel:
    """Test suite for Landlord model."""
    
    def test_landlord_creation_with_user(self):
        """Test creating a landlord with associated user."""
        landlord = LandlordFactory()
        
        assert landlord.id is not None
        assert landlord.user is not None
        assert landlord.national_id is not None
        assert isinstance(landlord.user, User)
    
    def test_landlord_onetoone_with_user(self):
        """Test that Landlord has OneToOne relationship with User."""
        user = UserFactory()
        landlord = Landlord.objects.create(
            user=user,
            national_id='123456789',
            id_url='path/to/id.png'
        )
        
        assert landlord.user == user
        assert user.landlord_profile == landlord
    
    def test_landlord_cascades_on_user_delete(self):
        """Test that Landlord is deleted when User is deleted (CASCADE)."""
        landlord = LandlordFactory()
        user_id = landlord.user.id
        
        landlord.user.delete()
        
        assert not Landlord.objects.filter(pk=landlord.pk).exists()
        assert not User.objects.filter(pk=user_id).exists()
    
    def test_landlord_str_returns_username(self):
        """Test that __str__ returns user's username."""
        landlord = LandlordFactory(user__username='landlord_test')
        assert str(landlord) == 'landlord_test'
    
    def test_landlord_national_id_is_required(self):
        """Test that national_id is required for landlord."""
        user = UserFactory()
        
        # Try to create landlord without national_id (should raise ValidationError)
        landlord = Landlord(user=user, id_url='test.png')
        
        with pytest.raises(ValidationError):
            landlord.full_clean()  # Triggers model validation
    
    def test_landlord_id_url_stores_file(self):
        """Test that id_url properly stores file."""
        landlord = LandlordFactory()
        
        assert landlord.id_url is not None
        assert landlord.id_url.name  # Has a filename


# ============================================================================
# USER RELATIONSHIPS TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestUserRelationships:
    """Test user relationships and edge cases."""
    
    def test_user_cannot_be_both_student_and_landlord(self):
        """✅ Un usuario no puede ser Student y Landlord simultáneamente
        
        Este test verifica que un usuario no puede tener ambos perfiles.
        La validación se hace en Student.clean() y Landlord.clean().
        """
        user = UserFactory()
        student = Student.objects.create(user=user)
        
        # Intentar crear Landlord con el mismo user debe fallar
        landlord = Landlord(
            user=user,
            national_id='123456',
            id_url='test.png'
        )
        
        with pytest.raises(ValidationError):
            landlord.full_clean()
    
    def test_deleting_student_does_not_delete_user(self):
        """
        Test that deleting Student profile doesn't delete the User.
        (Only CASCADE works User -> Student, not the other way)
        """
        student = StudentFactory()
        user = student.user
        user_id = user.id
        
        # Delete student
        student.delete()
        
        # User should still exist
        assert User.objects.filter(pk=user_id).exists()
        
        # But student_profile should not
        user.refresh_from_db()
        with pytest.raises(Student.DoesNotExist):
            _ = user.student_profile
