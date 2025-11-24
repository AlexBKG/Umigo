from django import forms
from .models import Listing


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            'price',
            'location_text',
            'lat',
            'lng',
            'zone',
            'rooms',
            'bathrooms',
            'shared_with_people',
            'utilities_price',
            'available',
        ]
