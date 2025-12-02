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