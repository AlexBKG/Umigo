# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Student, Landlord


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Extendemos el admin de usuario estándar con nuestros campos extra
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extra info', {
            'fields': ('is_suspended', 'suspension_end_at'),
        }),
    )
    list_display = BaseUserAdmin.list_display + ('is_suspended',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')


@admin.register(Landlord)
class LandlordAdmin(admin.ModelAdmin):
    list_display = ('user', 'national_id', 'created_at')
