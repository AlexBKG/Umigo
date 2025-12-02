from django.db import models
from users.models import Landlord, Student
from django.conf import settings  # al inicio del archivo, si aún no está

class Zone(models.Model):
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.city}"

class Listing(models.Model):
    owner = models.ForeignKey(
        Landlord,
        on_delete=models.CASCADE,
        related_name='listings'
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    location_text = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT, related_name='listings')

    rooms = models.IntegerField()
    bathrooms = models.IntegerField()
    shared_with_people = models.IntegerField()
    utilities_price = models.DecimalField(max_digits=12, decimal_places=2)
    available = models.BooleanField(default=True)
    views = models.PositiveIntegerField(default=0)
    popularity = models.FloatField(default=0.0)

    favorited_by = models.ManyToManyField(Student, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.location_text} ({self.price})"

class ListingPhoto(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    url = models.URLField(max_length=300)
    mime_type = models.CharField(max_length=50)
    size_bytes = models.BigIntegerField()
    sort_order = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"Photo {self.id} for listing {self.listing_id}"
    

class Comment(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment {self.id} on listing {self.listing_id}'
    
class Review(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    author = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    text = models.TextField(max_length=1000)

    class StarRating(models.IntegerChoices):
        ONE_STAR = 1, "1 estrella"
        TWO_STARS = 2, "2 estrellas"
        THREE_STARS = 3, "3 estrellas"
        FOUR_STARS = 4, "4 estrellas"
        FIVE_STARS = 5, "5 estrellas"

    rating = models.IntegerField(choices=StarRating)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Review {self.id} on listing {self.listing_id}'