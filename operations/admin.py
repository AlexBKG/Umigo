from django.contrib import admin
from .models import Admin


@admin.register(Admin)
class AdminModelAdmin(admin.ModelAdmin):
    """
    Interface administrativa para el modelo Admin.
    Permite ver y gestionar los administradores que revisan reportes.
    """
    list_display = ('id', 'username_display', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Admin Information', {
            'fields': ('user',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def username_display(self, obj):
        """Display username from related User."""
        if obj.user:
            return obj.user.username
        return f"Admin #{obj.id}"
    username_display.short_description = 'Username'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion if Admin has reviewed reports."""
        if obj and obj.report_set.exists():
            return False
        return super().has_delete_permission(request, obj)

