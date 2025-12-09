from django import forms
from .models import Listing, Comment, Review


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Campos tipo texto/número
        text_like = [
            'price', 'location_text', 'lat', 'lng',
            'rooms', 'bathrooms', 'shared_with_people',
            'utilities_price',
        ]
        for name in text_like:
            if name in self.fields:
                self.fields[name].widget.attrs.update({
                    'class': 'form-control',
                })

        # Select de zona
        if 'zone' in self.fields:
            self.fields['zone'].widget.attrs.update({
                'class': 'form-select',
            })

        # Checkbox de disponible
        if 'available' in self.fields:
            self.fields['available'].widget.attrs.update({
                'class': 'form-check-input',
            })


class CommentForm(forms.ModelForm):
    parent = forms.ModelChoiceField(
        queryset=Comment.objects.all(),
        required=False,
        widget=forms.HiddenInput
    )

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


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Escribe tu reseña...'
            })
        }
        labels = {
            'text': 'Reseña'
        }

