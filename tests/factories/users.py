"""
Factory Boy factories for users models.

Creates test instances of User, Student, and Landlord.
"""
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from users.models import Student, Landlord

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """
    Factory for User model.
    
    Usage:
        user = UserFactory()
        user = UserFactory(username='custom', email='custom@test.com')
        users = UserFactory.create_batch(5)
    """
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    
    is_active = True
    is_staff = False
    is_superuser = False
    
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class StaffFactory(UserFactory):
    """
    Factory for staff users (without Admin profile).
    
    Usage:
        staff = StaffFactory()
        staff = StaffFactory(username='admin_user')
    """
    username = factory.Sequence(lambda n: f'staff{n}')
    is_staff = True
    is_superuser = False


class SuperuserFactory(UserFactory):
    """
    Factory for superuser.
    
    Usage:
        admin = SuperuserFactory()
    """
    username = factory.Sequence(lambda n: f'admin{n}')
    is_staff = True
    is_superuser = True


class StudentFactory(DjangoModelFactory):
    """
    Factory for Student model (with OneToOne User).
    
    Usage:
        student = StudentFactory()
        student = StudentFactory(user__username='johndoe')
        student = StudentFactory(user=existing_user)
    """
    class Meta:
        model = Student
    
    user = factory.SubFactory(UserFactory)


class LandlordFactory(DjangoModelFactory):
    """
    Factory for Landlord model (with OneToOne User).
    
    Usage:
        landlord = LandlordFactory()
        landlord = LandlordFactory(national_id='123456789')
        landlord = LandlordFactory(user__username='property_owner')
    """
    class Meta:
        model = Landlord
    
    user = factory.SubFactory(UserFactory)
    national_id = factory.Sequence(lambda n: f'ID{n:09d}')
    id_url = factory.django.FileField(
        filename='id_card.png',
        data=b'\x89PNG\r\n\x1a\n' + b'0' * 1024
    )
