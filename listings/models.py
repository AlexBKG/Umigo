from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from users.models import Landlord, Student
from django.db.models import Avg
from django.conf import settings  # al inicio del archivo, si aún no está

class Zone(models.Model):
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'zone'

    def __str__(self):
        return f"{self.name} - {self.city}"

class Listing(models.Model):
    owner = models.ForeignKey(
        Landlord,
        on_delete=models.CASCADE,
        related_name='listings'
    )
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(0, message="El precio no puede ser negativo")]
    )
    location_text = models.CharField(max_length=255)
    lat = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        validators=[
            MinValueValidator(-90, message="La latitud debe estar entre -90 y 90"),
            MaxValueValidator(90, message="La latitud debe estar entre -90 y 90")
        ],
        help_text="Latitud: -90 a 90 (Norte-Sur)"
    )
    lng = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        validators=[
            MinValueValidator(-180, message="La longitud debe estar entre -180 y 180"),
            MaxValueValidator(180, message="La longitud debe estar entre -180 y 180")
        ],
        help_text="Longitud: -180 a 180 (Este-Oeste)"
    )
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT, related_name='listings')

    rooms = models.IntegerField(
        validators=[MinValueValidator(1, message="Debe tener al menos 1 habitación")]
    )
    bathrooms = models.IntegerField(
        validators=[MinValueValidator(1, message="Debe tener al menos 1 baño")]
    )
    shared_with_people = models.IntegerField(
        validators=[MinValueValidator(0, message="No puede ser negativo")],
        help_text="Número de personas con las que se comparte (0 si es privado)"
    )
    utilities_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(0, message="El precio de servicios no puede ser negativo")]
    )
    available = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    popularity = models.FloatField(default=0.0)

    favorited_by = models.ManyToManyField(
        Student, 
        through='Favorite',
        blank=True,
        related_name='favorite_listings'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'listing'

    def notifyAvailabilityToStudents(self, domain):
        favoritedStudents = self.favorited_by.all()
        for student in favoritedStudents:
            student.receiveAvailabilityNotification(domain, self)
    
    def __str__(self):
        return f"{self.location_text} ({self.price})"

class ListingPhoto(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='listing_photos/', db_column='url')
    mime_type = models.CharField(max_length=50)
    size_bytes = models.BigIntegerField()
    sort_order = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'listing_photo'
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
    text = models.TextField(max_length=800)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='replies',
        on_delete=models.CASCADE,
        db_column='parent_comment_id'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'comment'
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
        related_name='reviews',
        db_column='student_id'
    )
    text = models.TextField(max_length=800)

    class StarRating(models.IntegerChoices):
        ONE_STAR = 1, "1 estrella"
        TWO_STARS = 2, "2 estrellas"
        THREE_STARS = 3, "3 estrellas"
        FOUR_STARS = 4, "4 estrellas"
        FIVE_STARS = 5, "5 estrellas"

    rating = models.IntegerField(choices=StarRating)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'review'
        ordering = ['-created_at']
        unique_together = [['author', 'listing']]

    def __str__(self):
        return f'Review {self.id} on listing {self.listing_id}'


class Favorite(models.Model):
    """Modelo intermedio para favoritos (Many-to-Many Listing ↔ Student)"""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'favorite'
        unique_together = [['student', 'listing']]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student.user.username} → Listing {self.listing_id}'