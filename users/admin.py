from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import AdminUserCreationForm, UserChangeForm
from .models import CustomUser, Student

# Register your models here.
class CustomUserAdmin(UserAdmin):
    add_form = AdminUserCreationForm
    form = UserChangeForm
    model = CustomUser
    list_display = [
        "email",
        "first_name",
        "last_name",
        "is_active",
    ]

admin.site.register(CustomUser, CustomUserAdmin)