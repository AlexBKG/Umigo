"""
URL configuration for inquiries app (reports system).
"""
from django.urls import path
from . import views

app_name = 'inquiries'

urlpatterns = [
    # Report forms (class-based views with permission mixins)
    path('report/user/<int:user_id>/', views.ReportUserFormView.as_view(), name='report_user'),
    path('report/listing/<int:listing_id>/', views.ReportListingFormView.as_view(), name='report_listing'),
]
