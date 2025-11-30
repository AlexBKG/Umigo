from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, View
)
from django.views.generic.edit import FormMixin
from django.db.models import Count, Avg
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib.sites.shortcuts import get_current_site

from .models import Listing, Comment
from .forms import ListingForm, CommentForm
from .mixins import LandlordRequiredMixin


# --------- VISTAS PÚBLICAS (estudiante / cualquiera) ----------

class ListingPublicListView(ListView):
    """
    Lista pública de anuncios para estudiantes/usuarios.
    """
    model = Listing
    template_name = 'listings/list_public.html'
    paginate_by = 12

    def get_queryset(self):
        qs = Listing.objects.filter(available=True)
        # aquí luego puedes agregar filtros por ciudad, zona, etc.
        return qs.order_by('-created_at')


class ListingDetailView(DetailView):
    """
    Detalle público de un anuncio.
    Aquí mostramos SIEMPRE los comentarios, y dejamos comentar a:
      - estudiantes (en cualquier anuncio)
      - landlord dueño del anuncio
    """
    model = Listing
    template_name = 'listings/detail.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # incrementar contador de vistas
        Listing.objects.filter(pk=obj.pk).update(views=models.F('views') + 1)
        obj.refresh_from_db(fields=['views'])
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        listing = self.object

        context['favorited_by'] = listing.favorited_by.count()

        # todos ven los comentarios del anuncio
        context['comments'] = (
            Comment.objects
            .filter(listing=listing)
            .select_related('author')
            .order_by('created_at')
        )

        # ¿puede el usuario comentar?
        user = self.request.user
        can_comment = False
        if user.is_authenticated:
            # es estudiante
            is_student = hasattr(user, 'student_profile')
            # es landlord
            landlord = getattr(user, 'landlord_profile', None)
            is_owner_landlord = bool(landlord and listing.owner_id == landlord.id)

            if is_student or is_owner_landlord:
                can_comment = True

        context['can_comment'] = can_comment
        context['comment_form'] = CommentForm()  # formulario vacío para el template

        # Can the user add/remove favorite?
        can_add_favorite = False
        can_remove_favorite = False
        if user.is_authenticated and hasattr(user, 'student_profile'):
            student = getattr(user, 'student_profile', None)
            is_favorited = listing.favorited_by.filter(pk=student.pk).exists()
            if is_favorited:
                can_remove_favorite = True
            else:
                can_add_favorite = True

        context['can_add_favorite'] = can_add_favorite
        context['can_remove_favorite'] = can_remove_favorite

        return context

def listingAddFavoriteView(request, pk):
    listing = get_object_or_404(Listing, pk=pk)

    if request.method == "POST":
        user = request.user
        student = getattr(user, 'student_profile', None)
        
        listing.favorited_by.add(student)

    return redirect('listings:listing_detail', pk=listing.pk)

def listingRemoveFavoriteView(request, pk):
    listing = get_object_or_404(Listing, pk=pk)

    if request.method == "POST":
        user = request.user
        student = getattr(user, 'student_profile', None)
        
        listing.favorited_by.remove(student)

    return redirect('listings:listing_detail', pk=listing.pk)

# --------- DASHBOARD DEL ARRENDADOR (OWNER) ----------

class LandlordListingListView(LandlordRequiredMixin, ListView):
    """
    Lista de anuncios del arrendador logueado.
    """
    template_name = 'listings/landlord_list.html'
    paginate_by = 20

    def get_queryset(self):
        landlord = self.request.user.landlord_profile
        return Listing.objects.filter(owner=landlord).order_by('-created_at')


class ListingCreateView(LandlordRequiredMixin, CreateView):
    model = Listing
    form_class = ListingForm
    template_name = 'listings/form.html'

    def form_valid(self, form):
        landlord = self.request.user.landlord_profile
        form.instance.owner = landlord
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('listings:landlord_listing_list')


class ListingUpdateView(LandlordRequiredMixin, UpdateView):
    model = Listing
    form_class = ListingForm
    template_name = 'listings/form.html'

    def get_queryset(self):
        landlord = self.request.user.landlord_profile
        return Listing.objects.filter(owner=landlord)

    def get_success_url(self):
        return reverse_lazy('listings:landlord_listing_list')


class ListingDeleteView(LandlordRequiredMixin, DeleteView):
    model = Listing
    template_name = 'listings/confirm_delete.html'
    success_url = reverse_lazy('listings:landlord_listing_list')

    def get_queryset(self):
        landlord = self.request.user.landlord_profile
        return Listing.objects.filter(owner=landlord)


class ListingToggleAvailabilityView(LandlordRequiredMixin, View):
    """
    Cambia disponible <-> no disponible (solo del owner).
    """
    def post(self, request, pk):
        landlord = request.user.landlord_profile
        listing = get_object_or_404(Listing, pk=pk, owner=landlord)
        listing.available = not listing.available
        listing.save(update_fields=['available'])

        if listing.available:
            listing.notifyAvailabilityToStudents(get_current_site(request).domain)
        return redirect('listings:landlord_listing_list')


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'listings/comment_confirm_delete.html'

    def get_success_url(self):
        # regresar al detalle del anuncio
        return reverse_lazy('listings:listing_detail', kwargs={'pk': self.object.listing_id})

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        user = request.user

        # ¿Es el autor del comentario?
        is_author = (comment.author == user)

        # ¿Es el arrendador dueño del anuncio?
        # Asumo que Landlord tiene un campo OneToOne llamado "user"
        # y Listing.owner es un Landlord.
        has_landlord_profile = hasattr(user, 'landlord_profile')
        is_listing_owner = has_landlord_profile and (comment.listing.owner == user.landlord_profile)

        if user.is_superuser or is_author or is_listing_owner:
            return super().dispatch(request, *args, **kwargs)

        return HttpResponseForbidden("No tienes permiso para eliminar este comentario.")


class LandlordListingStatsView(LandlordRequiredMixin, ListView):
    """
    Estadísticas básicas del arrendador.
    (Por ahora solo vistas; luego podrás añadir favoritos/reviews.)
    """
    template_name = 'listings/landlord_stats.html'

    def get_queryset(self):
        landlord = self.request.user.landlord_profile
        return (
            Listing.objects.filter(owner=landlord)
            .order_by('-views')
        )

class CommentCreateView(View):
    """
    Crea un comentario para un listing.
    Permite:
      - estudiantes (en cualquier anuncio)
      - landlord dueño del anuncio
    """
    def post(self, request, pk):
        listing = get_object_or_404(Listing, pk=pk)

        if not request.user.is_authenticated:
            raise PermissionDenied("Debe iniciar sesión para comentar.")

        user = request.user
        is_student = hasattr(user, 'student_profile')
        landlord = getattr(user, 'landlord_profile', None)
        is_owner_landlord = bool(landlord and listing.owner_id == landlord.id)

        if not (is_student or is_owner_landlord):
            # ni estudiante, ni landlord dueño -> no puede comentar
            raise PermissionDenied("No tiene permiso para comentar en este anuncio.")

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.listing = listing
            comment.author = user
            comment.save()

        return redirect('listings:listing_detail', pk=listing.pk)
