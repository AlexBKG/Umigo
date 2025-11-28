from django.db import models
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView,
    CreateView, UpdateView, DeleteView, View
)
from django.db.models import Count, Avg

from .models import Listing
from .forms import ListingForm
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
    """
    model = Listing
    template_name = 'listings/detail.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # incrementar contador de vistas
        Listing.objects.filter(pk=obj.pk).update(views=models.F('views') + 1)
        obj.refresh_from_db(fields=['views'])
        return obj


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
        return redirect('listings:landlord_listing_list')


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

