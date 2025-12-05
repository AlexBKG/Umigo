import re
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserChangeForm, UserCreationForm, SetPasswordForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _

from .models import User, Student, Landlord

class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(label = "Correo")
    first_name = forms.CharField(label = "Nombre")
    last_name = forms.CharField(label = "Apellidos")
    is_active = forms.BooleanField(label = "Activo", help_text = "Permite al usuario ingresar a su cuenta, deselecciónalo si el usuario debería estar suspendido", required=False)
    suspension_end_at = forms.DateField(label = "Fecha de fin de la suspensión", required=False, help_text = "La fecha en la que se termina la suspensión del usuario, déjalo vacío si el usuario no está suspendido")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "suspension_end_at")

    def save(self, commit=True):
        user = super(CustomUserChangeForm, self).save(commit=False)
        user.username = self.cleaned_data["first_name"] + " " + self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user

class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True

    password1 = forms.CharField(
        label="Contraseña",
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        required=True,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text=_("Ingresa la misma contraseña que antes, para verificar."),
    )

    error_messages = {
        **UserCreationForm.error_messages,
        "password_mismatch": "Las dos contraseñas no coinciden",
    }

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password1", "password2"]
        labels = {
            "email": _("Correo"),
            "first_name": _("Nombre"),
            "last_name": _("Apellidos"),
        }

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.username = re.sub("  +", " ", self.cleaned_data["first_name"]) + " " + re.sub("  +", " ", self.cleaned_data["last_name"])

        if commit:
            user.save()
        return user
    
class LandlordCreationForm(forms.ModelForm):
    national_id = forms.CharField(label = "Número de documento", max_length=20)
    id_url = forms.FileField(label = "Carga de documento")

    class Meta:
        model = Landlord
        fields = ["national_id", "id_url"]

class PasswordForm(SetPasswordForm):
    error_messages = {
        **SetPasswordForm.error_messages,
        "password_mismatch": "Las contraseñas no coinciden.",  # your custom text
    }

class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": _(
            "Por favor ingresa un nombre de usuario y contraseña correctos, asegúrate de que estén bien "
            "escritos incluyendo mayúsculas."
        ),
        "inactive": _("Esta cuenta no se encuentra activa, revisa tu correo para activarla con el enlace que enviamos en tu proceso de registro."),
    }