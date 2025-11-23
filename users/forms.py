from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Student, Landlord


class CustomUserCreationForm(AdminUserCreationForm):
    email = forms.EmailField(label = "Correo")
    first_name = forms.CharField(label = "Nombre")
    last_name = forms.CharField(label = "Apellidos")

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email")

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.username = self.cleaned_data["first_name"] + " " + self.cleaned_data["last_name"]

        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(label = "Correo")
    first_name = forms.CharField(label = "Nombre")
    last_name = forms.CharField(label = "Apellidos")

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email")

    def save(self, commit=True):
        user = super(CustomUserChangeForm, self).save(commit=False)
        user.username = self.cleaned_data["first_name"] + " " + self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user

class AdminStudentCreationForm(AdminUserCreationForm):
    email = forms.EmailField(label = "Correo")
    first_name = forms.CharField(label = "Nombre")
    last_name = forms.CharField(label = "Apellidos")

    class Meta:
        model = Student
        fields = ("first_name", "last_name", "email")

    def save(self, commit=True):
        user = super(AdminStudentCreationForm, self).save(commit=False)
        user.username = self.cleaned_data["first_name"] + " " + self.cleaned_data["last_name"]

        students_group, created = Group.objects.get_or_create(name = 'Students')
        user.groups.add(students_group)

        if commit:
            user.save()
        return user

class StudentChangeForm(UserChangeForm):
    email = forms.EmailField(label = "Correo")
    first_name = forms.CharField(label = "Nombre")
    last_name = forms.CharField(label = "Apellidos")

    class Meta:
        model = Student
        fields = ("first_name", "last_name", "email")

    def save(self, commit=True):
        user = super(StudentChangeForm, self).save(commit=False)
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
        model = CustomUser
        fields = ["first_name", "last_name", "email", "password1", "password2"]
        labels = {
            "email": _("Correo"),
            "first_name": _("Nombre"),
            "last_name": _("Apellidos"),
        }

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.username = self.cleaned_data["first_name"] + " " + self.cleaned_data["last_name"]

        if commit:
            user.save()
        return user
    
class StudentCreationForm(CustomUserCreationForm):
    class Meta(CustomUserCreationForm.Meta):
        model = Student        

    def save(self, commit=True):
        user = super(StudentCreationForm, self).save(commit=False)
        user.username = self.cleaned_data["first_name"] + " " + self.cleaned_data["last_name"]

        if commit:
            user.save()

        students_group, created = Group.objects.get_or_create(name = 'Students')
        user.groups.add(students_group)

        return user

class LandlordCreationForm(CustomUserCreationForm):
    identificationType = forms.CharField(label = "Tipo de documento")
    identificationNumber = forms.CharField(label = "Número de documento")
    identificationCard = forms.FileField(label = "Carga de documento")

    class Meta(CustomUserCreationForm.Meta):
        model = Landlord
        fields = ["first_name", "last_name", "email", "password1", "password2", "identificationType", "identificationNumber", "identificationCard"]

    def save(self, commit=True):
        user = super(LandlordCreationForm, self).save(commit=False)
        user.username = self.cleaned_data["first_name"] + " " + self.cleaned_data["last_name"]

        if commit:
            user.save()

        #landlords_group, created = Group.objects.get_or_create(name = 'Landlords') Opted for manually adding the landlord group and its permissions, so admins can verify identification
        #user.groups.add(landlords_group)

        return user