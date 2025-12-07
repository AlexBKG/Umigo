from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError

from .forms import ReportForm
from .services import ReportService
from .mixins import CanReportMixin, StudentRequiredMixin
from users.models import User
from listings.models import Listing


@method_decorator(csrf_protect, name='dispatch')
class ReportUserFormView(CanReportMixin, FormView):
    """
    View for reporting a user (student or landlord).
    Both students and landlords can report users.
    Processes POST from modal in detail.html, no template rendering.
    """
    form_class = ReportForm
    
    def dispatch(self, request, *args, **kwargs):
        self.reported_user = get_object_or_404(User, pk=self.kwargs['user_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # If accessed via GET (no modal/JS), redirect back with message
        messages.info(request, 'Por favor usa el botón de reporte en la página correspondiente.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['reporter'] = self.request.user
        kwargs['target_type'] = 'USER'
        kwargs['target_id'] = self.reported_user.id
        return kwargs
    
    def form_valid(self, form):
        try:
            ReportService.create_report(
                reporter=self.request.user,
                reason=form.cleaned_data['reason'],
                target_type='USER',
                target_id=self.reported_user.id
            )
            messages.success(self.request, 'Tu reporte fue enviado para revisión.')
        except ValidationError as e:
            # Extract message without brackets from ValidationError
            error_msg = e.messages[0] if hasattr(e, 'messages') and e.messages else str(e)
            messages.error(self.request, error_msg)
        except Exception as e:
            messages.error(self.request, str(e))
        
        return redirect(self.get_success_url())
    
    def form_invalid(self, form):
        # Show form errors as messages and redirect back
        for field, errors in form.errors.items():
            for error in errors:
                # Convert ValidationError to string to remove brackets
                messages.error(self.request, str(error))
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        # Use 'next' from POST or referer
        next_url = self.request.POST.get('next') or self.request.META.get('HTTP_REFERER', '/')
        return next_url


@method_decorator(csrf_protect, name='dispatch')
class ReportListingFormView(StudentRequiredMixin, FormView):
    """
    View for reporting a listing.
    Only students can report listings.
    Processes POST from modal in detail.html, no template rendering.
    """
    form_class = ReportForm
    
    def dispatch(self, request, *args, **kwargs):
        self.listing = get_object_or_404(Listing, pk=self.kwargs['listing_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # If accessed via GET, redirect to listing detail
        messages.info(request, 'Por favor usa el botón de reporte en el detalle de la publicación.')
        return redirect('listings:listing_detail', pk=self.listing.pk)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['reporter'] = self.request.user
        kwargs['target_type'] = 'LISTING'
        kwargs['target_id'] = self.listing.id
        return kwargs
    
    def form_valid(self, form):
        try:
            ReportService.create_report(
                reporter=self.request.user,
                reason=form.cleaned_data['reason'],
                target_type='LISTING',
                target_id=self.listing.id
            )
            messages.success(self.request, 'Tu reporte sobre la publicación fue enviado.')
        except ValidationError as e:
            # Extract message without brackets from ValidationError
            error_msg = e.messages[0] if hasattr(e, 'messages') and e.messages else str(e)
            messages.error(self.request, error_msg)
        except Exception as e:
            messages.error(self.request, str(e))
        
        return redirect(self.get_success_url())
    
    def form_invalid(self, form):
        # Show form errors as messages and redirect back
        for field, errors in form.errors.items():
            for error in errors:
                # Convert ValidationError to string to remove brackets
                messages.error(self.request, str(error))
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        # Use 'next' from POST or default to listing detail
        next_url = self.request.POST.get('next') or reverse_lazy('listings:listing_detail', kwargs={'pk': self.listing.pk})
        return next_url
