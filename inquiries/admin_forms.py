"""
Custom ModelForm for Report admin interface.
Handles auto-assignment of reviewed_by before model validation.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Report
from operations.models import Admin


class ReportAdminForm(forms.ModelForm):
    """
    Form for Report model in admin interface.
    Auto-assigns reviewed_by to current staff user when status changes to ACCEPTED/REJECTED.
    """
    
    class Meta:
        model = Report
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Injected by ModelAdmin
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Validate and auto-assign reviewer BEFORE model.clean() is called.
        This ensures the validation in Report.clean() passes.
        """
        cleaned = super().clean()
        status = cleaned.get('status')
        reviewed_by = cleaned.get('reviewed_by')

        # If status is ACCEPTED/REJECTED and no reviewer assigned
        if status in ('ACCEPTED', 'REJECTED') and not reviewed_by:
            if not self.request or not self.request.user.is_staff:
                raise ValidationError("Solo un usuario staff puede resolver reportes.")

            # Get or create Admin profile for current user
            admin_obj = getattr(self.request.user, 'admin_profile', None)
            if admin_obj is None:
                admin_obj = Admin.objects.create(user=self.request.user)

            # Assign in both cleaned_data and instance (for model.clean to see it)
            cleaned['reviewed_by'] = admin_obj
            self.instance.reviewed_by = admin_obj

        return cleaned
