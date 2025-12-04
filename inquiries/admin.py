from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db import transaction
from .models import Report, UserReport, ListingReport


@admin.register(Report)
class ReportAdmin(ModelAdmin):
    """
    Admin interface for managing reports with bulk actions and filters.
    Provides actions to accept or reject reports in bulk.
    
    AUTO-MODERATION (triggers automatically when accepting reports against users):
        - 1st ACCEPTED report → User suspended for 30 days (suspension_end_at = today + 30 days)
        - 2+ ACCEPTED reports → User account deleted
        
    IMPORTANT: users_user.suspension_end_at is DATE field (not DATETIME)
    Database schema: suspension_end_at DATE NULL
    
    Note: Moderation is handled by Report.save() in models.py
    """
    list_display = ('id', 'reporter_link', 'report_type_display', 'target_display', 'reason_short', 'status', 'created_at', 'reviewed_by_link')
    list_filter = ('status', 'report_type', 'created_at', 'updated_at')
    search_fields = ('reason', 'reporter__username', 'reporter__email')
    readonly_fields = ('reporter', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    actions = ['accept_reports', 'reject_reports']

    fieldsets = (
        ('Report Information', {
            'fields': ('reporter', 'report_type', 'reason', 'status')
        }),
        ('Review Information', {
            'fields': ('reviewed_by',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def report_type_display(self, obj):
        """Display report type with icon."""
        icons = {
            'FRAUD': '💰',
            'HARASSMENT': '⚠️',
            'INAPPROPRIATE_LANGUAGE': '🗣️',
            'MISLEADING_CONTENT': '❌',
            'OTHER': '📝',
        }
        icon = icons.get(obj.report_type, '📝')
        label = obj.get_report_type_display()
        return format_html('{} {}', icon, label)
    report_type_display.short_description = 'Tipo'

    def reporter_link(self, obj):
        """Link to reporter's user admin page."""
        if obj.reporter:
            url = reverse('admin:users_user_change', args=[obj.reporter.pk])
            return format_html('<a href="{}">{}</a>', url, obj.reporter.username)
        return '-'
    reporter_link.short_description = 'Reporter'

    def target_display(self, obj):
        """Display the target (user or listing) with admin link."""
        try:
            user_report = UserReport.objects.get(report_id=obj.id)
            if user_report.reported_user:
                url = reverse('admin:users_user_change', args=[user_report.reported_user.pk])
                return format_html('👤 <a href="{}">User: {}</a>', url, user_report.reported_user.username)
        except UserReport.DoesNotExist:
            pass

        try:
            listing_report = ListingReport.objects.get(report_id=obj.id)
            if listing_report.listing:
                url = reverse('admin:listings_listing_change', args=[listing_report.listing.pk])
                return format_html('🏠 <a href="{}">Listing: {}</a>', url, listing_report.listing.location_text)
        except ListingReport.DoesNotExist:
            pass

        return '-'
    target_display.short_description = 'Target'

    def reason_short(self, obj):
        """Truncate reason for list display."""
        if len(obj.reason) > 50:
            return obj.reason[:50] + '...'
        return obj.reason
    reason_short.short_description = 'Reason'

    def reviewed_by_link(self, obj):
        """Link to reviewer's admin user page."""
        if obj.reviewed_by:
            url = reverse('admin:operations_admin_change', args=[obj.reviewed_by.pk])
            username = obj.reviewed_by.user.username if obj.reviewed_by.user else f"Admin #{obj.reviewed_by.pk}"
            return format_html('<a href="{}">{}</a>', url, username)
        return '-'
    reviewed_by_link.short_description = 'Reviewed By'
    
    def save_model(self, request, obj, form, change):
        """
        Auto-assign reviewed_by to current admin when status changes from UNDER_REVIEW.
        """
        if change:  # Only for existing reports
            old_status = Report.objects.get(pk=obj.pk).status
            new_status = obj.status
            
            # If status changed from UNDER_REVIEW to ACCEPTED/REJECTED
            if old_status == 'UNDER_REVIEW' and new_status in ('ACCEPTED', 'REJECTED'):
                if not obj.reviewed_by:
                    # Get or create Admin instance for current user
                    from operations.models import Admin
                    admin_obj, created = Admin.objects.get_or_create(
                        user=request.user
                    )
                    obj.reviewed_by = admin_obj
        
        super().save_model(request, obj, form, change)

    @admin.action(description='✅ Accept selected reports')
    def accept_reports(self, request, queryset):
        """Bulk action to accept reports."""
        with transaction.atomic():
            count = 0
            for report in queryset.filter(status='PENDING'):
                report.status = 'ACCEPTED'
                report.save()
                count += 1
        self.message_user(request, f'{count} report(s) accepted successfully.')

    @admin.action(description='❌ Reject selected reports')
    def reject_reports(self, request, queryset):
        """Bulk action to reject reports."""
        with transaction.atomic():
            count = 0
            for report in queryset.filter(status='PENDING'):
                report.status = 'REJECTED'
                report.save()
                count += 1
        self.message_user(request, f'{count} report(s) rejected successfully.')


@admin.register(UserReport)
class UserReportAdmin(ModelAdmin):
    """Admin interface for UserReport with links to related objects."""
    list_display = ('report', 'reported_user_link', 'created_at')
    readonly_fields = ('report', 'reported_user')
    search_fields = ('reported_user__username', 'report__reason')

    def reported_user_link(self, obj):
        if obj.reported_user:
            url = reverse('admin:users_user_change', args=[obj.reported_user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.reported_user.username)
        return '-'
    reported_user_link.short_description = 'Reported User'

    def created_at(self, obj):
        return obj.report.created_at if obj.report else '-'
    created_at.short_description = 'Created At'


@admin.register(ListingReport)
class ListingReportAdmin(ModelAdmin):
    """Admin interface for ListingReport with links to related objects."""
    list_display = ('report', 'listing_link', 'created_at')
    readonly_fields = ('report', 'listing')
    search_fields = ('listing__location_text', 'report__reason')

    def listing_link(self, obj):
        if obj.listing:
            url = reverse('admin:listings_listing_change', args=[obj.listing.pk])
            return format_html('<a href="{}">{}</a>', url, obj.listing.location_text)
        return '-'
    listing_link.short_description = 'Listing'

    def created_at(self, obj):
        return obj.report.created_at if obj.report else '-'
    created_at.short_description = 'Created At'
