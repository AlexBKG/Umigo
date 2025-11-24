from django.urls import path
from . import views

urlpatterns = [
    # Público
    path('', views.ListingPublicListView.as_view(), name='listing_public_list'),
    path('listing/<int:pk>/', views.ListingDetailView.as_view(), name='listing_detail'),

    # Landlord
    path('landlord/listings/', views.LandlordListingListView.as_view(), name='landlord_listing_list'),
    path('landlord/listings/new/', views.ListingCreateView.as_view(), name='listing_create'),
    path('landlord/listings/<int:pk>/edit/', views.ListingUpdateView.as_view(), name='listing_update'),
    path('landlord/listings/<int:pk>/delete/', views.ListingDeleteView.as_view(), name='listing_delete'),
    path('landlord/listings/<int:pk>/toggle/', views.ListingToggleAvailabilityView.as_view(), name='listing_toggle'),
    path('landlord/listings/stats/', views.LandlordListingStatsView.as_view(), name='landlord_listing_stats'),
]
