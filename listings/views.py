from django.db import models
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, View
)
from django.views.generic.edit import FormMixin
from django.db.models import Count, Avg
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Listing, ListingPhoto, Comment
from .forms import ListingForm, CommentForm
from .mixins import LandlordRequiredMixin
from users.models import Landlord, Student
from django.core.exceptions import PermissionDenied


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
        user = self.request.user

        context['comments'] = (
            Comment.objects
            .filter(listing=listing, parent__isnull=True)
            .select_related('author')
            .prefetch_related('replies__author')
            .order_by('created_at')
        )

        is_student = user.is_authenticated and hasattr(user, 'student_profile')
        landlord = getattr(user, 'landlord_profile', None) if user.is_authenticated else None
        is_owner_landlord = bool(landlord and listing.owner_id == landlord.id)

        # ¿puede comentar?
        can_comment = user.is_authenticated and (is_student or is_owner_landlord)
        context['can_comment'] = can_comment

        # URL de regreso según quién está viendo
        # (si es el dueño -> "Mis arriendos"; si no -> lista pública)
        context['back_url'] = (
            'listings:landlord_listing_list'  
            if is_owner_landlord
            else 'listings:listing_public_list'
        )

        # formulario de comentario vacío
        context['comment_form'] = CommentForm()

        return context


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
        # Validamos aquí las imágenes
        images = self.request.FILES.getlist('images')
        min_photos = 1
        max_photos = 5

        if len(images) < min_photos:
            form.add_error(None, 'Debes subir al menos una foto.')
            return self.form_invalid(form)

        if len(images) > max_photos:
            form.add_error(None, f'Solo se permiten máximo {max_photos} fotos.')
            return self.form_invalid(form)
    
        landlord = self.request.user.landlord_profile
        form.instance.owner = landlord

        # Primero guardamos el Listing
        response = super().form_valid(form)

        for img in images:
            ListingPhoto.objects.create(listing=self.object, image=img)

        return response

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('listings:landlord_listing_list')


class ListingUpdateView(LandlordRequiredMixin, UpdateView):
    model = Listing
    form_class = ListingForm
    template_name = 'listings/form.html'

    def form_valid(self, form):
        request = self.request
        listing = self.object  # el que se está editando

        # Fotos actuales del anuncio
        current_photos_qs = listing.photos.all()
        current_count = current_photos_qs.count()

        # Fotos marcadas para eliminar
        delete_ids = request.POST.getlist('delete_photos')  # lista de strings
        to_delete_qs = current_photos_qs.filter(id__in=delete_ids)
        delete_count = to_delete_qs.count()

        # Nuevas fotos que se van a subir
        new_images = request.FILES.getlist('images')
        new_count = len(new_images)

        # Reglas de negocio
        min_photos = 1
        max_photos = 5

        remaining_after_delete = current_count - delete_count
        total_after = remaining_after_delete + new_count

        if total_after < min_photos:
            form.add_error(
                None,
                'El anuncio debe tener al menos una foto. '
                'Sube una nueva imagen o desmarca alguna que quieras eliminar.'
            )
            return self.form_invalid(form)

        if total_after > max_photos:
            form.add_error(
                None,
                f'El anuncio no puede tener más de {max_photos} fotos en total. '
                f'Actualmente quedarán {total_after}.'
            )
            return self.form_invalid(form)

        # Hasta aquí las reglas se cumplen: aplicamos cambios
        # 1) Guardamos cambios básicos del Listing
        response = super().form_valid(form)

        # 2) Eliminamos las fotos marcadas
        to_delete_qs.delete()

        # 3) Creamos las nuevas fotos
        for img in new_images:
            ListingPhoto.objects.create(listing=self.object, image=img)

        return response

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

        # 1. Debe estar autenticado
        if not request.user.is_authenticated:
            raise PermissionDenied("Debe iniciar sesión para comentar.")

        user = request.user

        # 2. ¿Quién es?
        is_student = hasattr(user, 'student_profile')
        landlord = getattr(user, 'landlord_profile', None)
        is_owner_landlord = bool(landlord and listing.owner_id == landlord.id)

        # 3. Solo estudiante o landlord dueño del anuncio pueden comentar
        if not (is_student or is_owner_landlord):
            raise PermissionDenied("No tiene permiso para comentar en este anuncio.")

        # 4. Procesar formulario (comentario nuevo o respuesta)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.listing = listing
            comment.author = user

            # *** NUEVO: soporte para respuestas (comentarios anidados) ***
            parent = form.cleaned_data.get("parent")  # viene del campo hidden
            if parent is not None:
                # Por seguridad, solo permitimos responder comentarios de este mismo listing
                if parent.listing_id == listing.id:
                    comment.parent = parent

            comment.save()

        # Puedes redirigir al detalle del anuncio
        return redirect('listings:listing_detail', pk=listing.pk)
    
    