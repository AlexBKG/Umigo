from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm
from .models import User, Student, Landlord

class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    verbose_name_plural = "Students"

    def get_extra(self, request, obj=None, **kwargs):
        return 0 if obj and hasattr(obj, "student_profile") else 1

class LandlordInline(admin.StackedInline):
    model = Landlord
    can_delete = False
    verbose_name_plural = "Landlords"

    def get_extra(self, request, obj=None, **kwargs):
        return 0 if obj and hasattr(obj, "landlord_profile") else 1

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    model = User

    fieldsets = (
        ("Información personal", {"fields": ("first_name", "last_name", "email")}),
        ("Suspensión", {"fields": ("is_active", "suspension_end_at")}),
        ("Permisos", {"fields": ("groups","user_permissions")}),
        ("Permisos extra", {"fields": ("is_staff","is_superuser")}),
    )

    list_display = [
        "email",
        "username",
        "is_active",
        "suspension_end_at",
    ]

    def get_inlines(self, request, obj=None):
        if not obj:
            return []

        if hasattr(obj, "student_profile"):
            return [StudentInline]

        if hasattr(obj, "landlord_profile"):
            return [LandlordInline]

        return []

admin.site.register(User, CustomUserAdmin)