from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import FormView
from django.urls import reverse_lazy

from .forms import ReportForm
from .services import ReportService
from .mixins import CanReportMixin, StudentRequiredMixin
from users.models import User
from listings.models import Listing


class ReportUserFormView(CanReportMixin, FormView):
    """
    View for reporting a user (student or landlord).
    Both students and landlords can report users.
    """
    template_name = 'inquiries/report_form.html'
    form_class = ReportForm
    
    def dispatch(self, request, *args, **kwargs):
        self.reported_user = get_object_or_404(User, pk=self.kwargs['user_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['reporter'] = self.request.user
        kwargs['reported_user'] = self.reported_user
        return kwargs
    
    def form_valid(self, form):
        service = ReportService()
        result = service.create_user_report(
            reporter=self.request.user,
            reported_user=self.reported_user,
            reason=form.cleaned_data['reason']
        )
        
        if result['success']:
            messages.success(self.request, result['message'])
        else:
            messages.error(self.request, result['message'])
        
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER', reverse_lazy('home'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_type'] = 'usuario'
        context['target_name'] = self.reported_user.get_full_name() or self.reported_user.username
        return context


class ReportListingFormView(StudentRequiredMixin, FormView):
    """
    View for reporting a listing.
    Only students can report listings.
    """
    template_name = 'inquiries/report_form.html'
    form_class = ReportForm
    
    def dispatch(self, request, *args, **kwargs):
        self.listing = get_object_or_404(Listing, pk=self.kwargs['listing_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['reporter'] = self.request.user
        kwargs['listing'] = self.listing
        return kwargs
    
    def form_valid(self, form):
        service = ReportService()
        result = service.create_listing_report(
            reporter=self.request.user,
            listing=self.listing,
            reason=form.cleaned_data['reason']
        )
        
        if result['success']:
            messages.success(self.request, result['message'])
        else:
            messages.error(self.request, result['message'])
        
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('listings:listing_detail', kwargs={'pk': self.listing.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_type'] = 'publicación'
        context['target_name'] = self.listing.location_text
        return context
