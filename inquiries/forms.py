from django import forms
from django.core.exceptions import ValidationError
from .models import Report, UserReport, ListingReport
from users.models import User
from listings.models import Listing


class ReportForm(forms.ModelForm):
    """
    Form for creating reports against users or listings.
    Validates business rules: no self-reporting, no admin reporting, student-only for listings.
    """
    
    class Meta:
        model = Report
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'maxlength': 255,
                'placeholder': 'Describe el motivo de tu reporte (mín. 10, máx. 255 caracteres)',
                'id': 'report-reason-field'
            }),
        }
        labels = {
            'reason': 'Motivo del reporte',
        }
        help_texts = {
            'reason': 'Explica claramente por qué estás reportando. Sé específico.',
        }
    
    def __init__(self, *args, **kwargs):
        """
        Custom initialization to accept reporter, target_type, and target_id.
        
        Args:
            reporter (User): User creating the report
            target_type (str): 'USER' or 'LISTING'
            target_id (int): ID of the reported user or listing
        """
        self.reporter = kwargs.pop('reporter', None)
        self.target_type = kwargs.pop('target_type', None)
        self.target_id = kwargs.pop('target_id', None)
        super().__init__(*args, **kwargs)
    
    def clean_reason(self):
        """Validate reason field is not empty and within length."""
        reason = self.cleaned_data.get('reason', '').strip()
        
        if not reason:
            raise ValidationError('El motivo del reporte es obligatorio')
        
        if len(reason) < 10:
            raise ValidationError('El motivo debe tener al menos 10 caracteres')
        
        return reason
    
    def clean(self):
        """
        Comprehensive validation including business rules.
        """
        cleaned_data = super().clean()
        
        # Validate required context
        if not self.reporter:
            raise ValidationError('No se ha especificado el usuario que reporta')
        
        if not self.target_type or self.target_type not in ('USER', 'LISTING'):
            raise ValidationError('Tipo de objetivo inválido')
        
        if not self.target_id:
            raise ValidationError('No se ha especificado el objetivo del reporte')
        
        # Validate target exists
        if self.target_type == 'USER':
            try:
                target_user = User.objects.get(pk=self.target_id)
            except User.DoesNotExist:
                raise ValidationError('El usuario reportado no existe')
            
            # Business rule: cannot report yourself
            if target_user == self.reporter:
                raise ValidationError('No puedes reportarte a ti mismo')
            
            # Business rule: cannot report administrators
            if target_user.is_staff or target_user.is_superuser:
                raise ValidationError('No se pueden reportar administradores')
        
        elif self.target_type == 'LISTING':
            try:
                target_listing = Listing.objects.get(pk=self.target_id)
            except Listing.DoesNotExist:
                raise ValidationError('La publicación reportada no existe')
            
            # Business rule: only students can report listings
            student_profile = getattr(self.reporter, 'student_profile', None)
            if student_profile is None:
                raise ValidationError('Solo los estudiantes pueden reportar publicaciones')
            
            # Business rule: cannot report your own listing
            landlord_profile = getattr(self.reporter, 'landlord_profile', None)
            if landlord_profile and target_listing.landlord == landlord_profile:
                raise ValidationError('No puedes reportar tu propia publicación')
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Save the report and create the appropriate UserReport or ListingReport.
        This is a basic save - for production use the services layer instead.
        """
        report = super().save(commit=False)
        report.reporter = self.reporter
        
        if commit:
            report.save()
            
            # Create the specific report type (UserReport or ListingReport)
            if self.target_type == 'USER':
                UserReport.objects.create(
                    report=report,
                    reported_user_id=self.target_id
                )
            elif self.target_type == 'LISTING':
                ListingReport.objects.create(
                    report=report,
                    listing_id=self.target_id
                )
        
        return report
