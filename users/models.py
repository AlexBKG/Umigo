from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class Report(models.Model):
    pass

class Listing(models.Model):
    pass

class CustomUser(AbstractUser):
    #__isSuspended = models.BooleanField() #Seems like is_active field works for this purpose
    suspensionEndDate = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.username
    
class Student(CustomUser):
    favoriteListings = models.ManyToManyField(Listing, blank=True)

    def __str__(self):
        return self.username
    
class Landlord(CustomUser):
    identificationType = models.CharField()
    identificationNumber = models.CharField()
    identificationCard = models.FileField(upload_to='identificationCards')
    listings = models.ManyToManyField(Listing, blank=True)

    def __str__(self):
        return self.username