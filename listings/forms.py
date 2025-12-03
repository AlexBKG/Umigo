from django import forms
from django.forms import ClearableFileInput
from .models import Listing, Comment


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


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

    def clean_images(self):
        images = self.files.getlist('images')
        if not images:
            raise forms.ValidationError('Debes subir al menos una foto.')
        if len(images) > 5:
            raise forms.ValidationError('Solo se permiten máximo 5 fotos.')
        return images

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