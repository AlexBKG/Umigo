"""
Factory Boy factories for listings models.

Creates test instances of Zone, Listing, ListingPhoto, Review, Comment, Favorite.
"""
import random
import factory
from factory.django import DjangoModelFactory
from django.core.files.base import ContentFile
from listings.models import (
    Zone, Listing, ListingPhoto,
    Review, Comment, Favorite
)
from .users import LandlordFactory, StudentFactory, UserFactory


class ZoneFactory(DjangoModelFactory):
    """
    Factory for Zone model.
    
    Usage:
        zone = ZoneFactory()
        zone = ZoneFactory(name='Centro', city='Bogotá')
    """
    class Meta:
        model = Zone
        django_get_or_create = ('name', 'city')
    
    name = factory.Sequence(lambda n: f'Zone {n}')
    city = factory.Faker('city')


class ListingFactory(DjangoModelFactory):
    """
    Factory for Listing model.
    
    Creates a basic listing without photos (available=False by default).
    Use ListingPhotoFactory to add photos.
    
    Usage:
        listing = ListingFactory()
        listing = ListingFactory(owner=landlord, zone=zone)
        listing = ListingFactory(price=1500000, rooms=3)
    """
    class Meta:
        model = Listing
    
    owner = factory.SubFactory(LandlordFactory)
    # Seleccionar una zona existente de zones.json (IDs 1-20)
    zone = factory.LazyFunction(lambda: Zone.objects.get(pk=random.randint(1, 20)))
    
    price = factory.Faker('pydecimal', left_digits=7, right_digits=2, positive=True)
    location_text = factory.Faker('address')
    
    # Coordinates for Bogotá approximately
    lat = factory.Faker('pydecimal', left_digits=2, right_digits=6, min_value=4.0, max_value=4.9)
    lng = factory.Faker('pydecimal', left_digits=3, right_digits=6, min_value=-74.5, max_value=-73.5)
    
    rooms = factory.Faker('random_int', min=1, max=5)
    bathrooms = factory.Faker('random_int', min=1, max=3)
    shared_with_people = factory.Faker('random_int', min=0, max=4)
    utilities_price = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    
    available = False  # Default: not available until photos are added
    views = 0
    popularity = 0.0


class ListingPhotoFactory(DjangoModelFactory):
    """
    Factory for ListingPhoto model.
    
    Creates a valid PNG photo for a listing.
    
    Usage:
        photo = ListingPhotoFactory(listing=listing)
        photos = ListingPhotoFactory.create_batch(3, listing=listing)
    """
    class Meta:
        model = ListingPhoto
    
    listing = factory.SubFactory(ListingFactory)
    
    # Generate a simple valid PNG
    image = factory.django.ImageField(
        filename='listing_photo.png',
        format='PNG',
        width=800,
        height=600,
        color='blue'
    )
    
    mime_type = 'image/png'
    size_bytes = factory.LazyAttribute(lambda obj: len(obj.image.read()))
    sort_order = factory.Sequence(lambda n: n)
    
    @factory.post_generation
    def reset_file_pointer(obj, create, extracted, **kwargs):
        """Reset file pointer after reading size_bytes."""
        if create and obj.image:
            obj.image.seek(0)


class ReviewFactory(DjangoModelFactory):
    """
    Factory for Review model.
    
    Creates a review from a student for a listing.
    
    Usage:
        review = ReviewFactory(listing=listing, author=student)
        review = ReviewFactory(rating=5, text='Great place!')
    """
    class Meta:
        model = Review
    
    listing = factory.SubFactory(ListingFactory)
    author = factory.SubFactory(StudentFactory)
    
    rating = factory.Faker('random_int', min=1, max=5)
    text = factory.Faker('paragraph', nb_sentences=3)


class CommentFactory(DjangoModelFactory):
    """
    Factory for Comment model.
    
    Creates a comment on a listing.
    
    Usage:
        comment = CommentFactory(listing=listing, author=user)
        reply = CommentFactory(listing=listing, parent=comment)
    """
    class Meta:
        model = Comment
    
    listing = factory.SubFactory(ListingFactory)
    author = factory.SubFactory(UserFactory)
    
    text = factory.Faker('paragraph', nb_sentences=2)
    parent = None  # Set to another Comment for replies


class FavoriteFactory(DjangoModelFactory):
    """
    Factory for Favorite model.
    
    Creates a favorite relationship between student and listing.
    
    Usage:
        favorite = FavoriteFactory(student=student, listing=listing)
    """
    class Meta:
        model = Favorite
    
    student = factory.SubFactory(StudentFactory)
    listing = factory.SubFactory(ListingFactory)
