# urls.py
from django.urls import path
from . import views
from .views import license_check_view
from .views import extend_license_view

urlpatterns = [
    path('pinnacle-school-of-commerce-and-management', views.home_view, name='home'),  # Home view as the default path
    path('license_terms', views.license_terms_view, name='license_terms'),
    path('privacy_policy', views.privacy_policy_view, name='privacy_policy'),
    path('terms_and_conditions', views.terms_and_conditions_view, name='terms_and_conditions'),
    path('activate-license-check', views.license_check_view, name='license_check_view'),# Use a unique name
    path('extend-license', extend_license_view, name='extend_license_view'),
    path('license-check', views.license_check, name='license_check'),
    path('create-license', views.create_license_view, name='create_license_view'),

]

