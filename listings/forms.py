from django import forms
from .models import Listing, Comment


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
            # NO pongas 'images' aquí
        ]
        labels = {
            'price': 'Precio',
            'location_text': 'Dirección o ubicación',
            'lat': 'Latitud',
            'lng': 'Longitud',
            'zone': 'Zona',
            'rooms': 'Habitaciones',
            'bathrooms': 'Baños',
            'shared_with_people': 'Personas con las que se comparte',
            'utilities_price': 'Precio de servicios',
            'available': 'Disponible',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Escribe tu comentario...'
            })
        }
        labels = {
            'text': 'Comentario'
        }