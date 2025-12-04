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
        """Display report type."""
        return obj.get_report_type_display()
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

    @admin.action(description='Reject selected reports')
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
    """
    Admin interface for UserReport with links to related objects.
    Para editar STATUS y REVIEWED_BY, usa el link 'Edit Report' o ve a Reports directamente.
    """
    list_display = ('report_id', 'reporter_name', 'reported_user_link', 'report_type', 'status_display', 'created_at')
    list_filter = ('report__status', 'report__report_type', 'report__created_at')
    readonly_fields = ('report', 'reported_user', 'report_details')
    search_fields = ('reported_user__username', 'report__reason', 'report__reporter__username')
    
    def report_id(self, obj):
        """Display report ID number."""
        return obj.report.id if obj.report else '-'
    report_id.short_description = 'ID'
    
    def reporter_name(self, obj):
        """Display reporter username."""
        if obj.report and obj.report.reporter:
            return obj.report.reporter.username
        return '-'
    reporter_name.short_description = 'Reporter'
    
    def report_type(self, obj):
        """Display report type."""
        if obj.report:
            return obj.report.get_report_type_display()
        return '-'
    report_type.short_description = 'Type'
    
    def status_display(self, obj):
        """Display status."""
        if obj.report:
            return obj.report.get_status_display()
        return '-'
    status_display.short_description = 'Status'

    def reported_user_link(self, obj):
        """Link to reported user's admin page."""
        if obj.reported_user:
            url = reverse('admin:users_user_change', args=[obj.reported_user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.reported_user.username)
        return '-'
    reported_user_link.short_description = 'Reported User'

    def created_at(self, obj):
        """Display creation timestamp."""
        return obj.report.created_at if obj.report else '-'
    created_at.short_description = 'Created At'
    
    def report_details(self, obj):
        """Display full report details in readonly view."""
        if not obj.report:
            return '-'
        
        r = obj.report
        
        html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">
            <h3 style="margin-top: 0;">Report #{r.id} - {r.get_report_type_display()}</h3>
            <p><strong>Reason:</strong> {r.reason}</p>
            <p><strong>Status:</strong> {r.get_status_display()}</p>
            <p><strong>Reporter:</strong> {r.reporter.username if r.reporter else '-'}</p>
            <p><strong>Created:</strong> {r.created_at.strftime('%Y-%m-%d %H:%M')}</p>
            <p><strong>Reviewed by:</strong> {r.reviewed_by if r.reviewed_by else 'Not yet reviewed'}</p>
            <hr>
            <a href="{reverse('admin:inquiries_report_change', args=[r.pk])}" 
               style="display: inline-block; padding: 8px 16px; background: #007bff; color: white; 
                      text-decoration: none; border-radius: 4px; font-weight: bold;">
                Edit This Report (Change Status/Reviewer)
            </a>
        </div>
        """
        return format_html(html)
    report_details.short_description = 'Report Details'


@admin.register(ListingReport)
class ListingReportAdmin(ModelAdmin):
    """
    Admin interface for ListingReport with links to related objects.
    Para editar STATUS y REVIEWED_BY, usa el link 'Edit Report' o ve a Reports directamente.
    """
    list_display = ('report_id', 'reporter_name', 'listing_link', 'report_type', 'status_display', 'created_at')
    list_filter = ('report__status', 'report__report_type', 'report__created_at')
    readonly_fields = ('report', 'listing', 'report_details')
    search_fields = ('listing__location_text', 'report__reason', 'report__reporter__username')
    
    def report_id(self, obj):
        """Display report ID number."""
        return obj.report.id if obj.report else '-'
    report_id.short_description = 'ID'
    
    def reporter_name(self, obj):
        """Display reporter username."""
        if obj.report and obj.report.reporter:
            return obj.report.reporter.username
        return '-'
    reporter_name.short_description = 'Reporter'
    
    def report_type(self, obj):
        """Display report type."""
        if obj.report:
            return obj.report.get_report_type_display()
        return '-'
    report_type.short_description = 'Type'
    
    def listing_link(self, obj):
        """Display status."""
        if obj.report:
            return obj.report.get_status_display()
        return '-'
    status_display.short_description = 'Status'

    def listing_link(self, obj):
        """Link to reported listing's admin page."""
        if obj.listing:
            url = reverse('admin:listings_listing_change', args=[obj.listing.pk])
            return format_html('<a href="{}">{}</a>', url, obj.listing.location_text)
        return '-'
    listing_link.short_description = 'Reported Listing'

    def created_at(self, obj):
        """Display creation timestamp."""
        return obj.report.created_at if obj.report else '-'
    created_at.short_description = 'Created At'
    
    def report_details(self, obj):
        """Display full report details in readonly view."""
        if not obj.report:
            return '-'
        
        r = obj.report
        
        html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745;">
            <h3 style="margin-top: 0;">Report #{r.id} - {r.get_report_type_display()}</h3>
            <p><strong>Reason:</strong> {r.reason}</p>
            <p><strong>Status:</strong> {r.get_status_display()}</p>
            <p><strong>Reporter:</strong> {r.reporter.username if r.reporter else '-'}</p>
            <p><strong>Created:</strong> {r.created_at.strftime('%Y-%m-%d %H:%M')}</p>
            <p><strong>Reviewed by:</strong> {r.reviewed_by if r.reviewed_by else 'Not yet reviewed'}</p>
            <hr>
            <a href="{reverse('admin:inquiries_report_change', args=[r.pk])}" 
               style="display: inline-block; padding: 8px 16px; background: #28a745; color: white; 
                      text-decoration: none; border-radius: 4px; font-weight: bold;">
                Edit This Report (Change Status/Reviewer)
            </a>
        </div>
        """
        return format_html(html)
    report_details.short_description = 'Report Details'
