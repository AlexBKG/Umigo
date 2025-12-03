from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    # Público
    path('listings/', views.ListingPublicListView.as_view(), name='listing_public_list'),
    path('listing/<int:pk>/', views.ListingDetailView.as_view(), name='listing_detail'),

    # Landlord
    path('landlord/listings/', views.LandlordListingListView.as_view(), name='landlord_listing_list'),
    path('landlord/listings/new/', views.ListingCreateView.as_view(), name='listing_create'),
    path('landlord/listings/<int:pk>/edit/', views.ListingUpdateView.as_view(), name='listing_update'),
    path('landlord/listings/<int:pk>/delete/', views.ListingDeleteView.as_view(), name='listing_delete'),
    path('landlord/listings/<int:pk>/toggle/', views.ListingToggleAvailabilityView.as_view(), name='listing_toggle'),
    path('landlord/listings/stats/', views.LandlordListingStatsView.as_view(), name='landlord_listing_stats'),

    #Comentarios
    path('listing/<int:pk>/comment/', views.CommentCreateView.as_view(), name='comment_create'),
    path('comment/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),

    #Reviews
    path('listing/<int:pk>/review/', views.ReviewCreateView.as_view(), name='review_create'),
    path('review/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review_delete'),
]
