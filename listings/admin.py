from django.contrib import admin
from .models import Zone, Listing, ListingPhoto


class ListingPhotoInline(admin.TabularInline):
    model = ListingPhoto
    extra = 1


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('location_text', 'price', 'available', 'views', 'owner', 'created_at')
    list_filter = ('available', 'zone__city', 'zone__name')
    search_fields = ('location_text', 'owner__user__username')
    inlines = [ListingPhotoInline]


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'city')


@admin.register(ListingPhoto)
class ListingPhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing', 'image', 'mime_type', 'size_bytes', 'sort_order', 'created_at']
