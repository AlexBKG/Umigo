from django.db import models
from users.models import Landlord, Student

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