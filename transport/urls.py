# transport/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('simulate-tracking/', views.simulate_bus_location, name='simulate_tracking'),

    path('master-transports/', views.master_transport_list, name='master_transport_list'),
    path('master-transports/add/', views.master_transport_create, name='master_transport_create'),
    path('master-transports/edit/<int:pk>/', views.master_transport_edit, name='master_transport_edit'),

    path('routes/', views.route_list, name='route_list'),
    path('routes/add/', views.route_create, name='route_create'),
    path('routes/edit/<int:pk>/', views.route_edit, name='route_edit'),

    path('stops/', views.stop_list, name='stop_list'),
    path('stops/add/', views.stop_create, name='stop_create'),
    path('stops/edit/<int:pk>/', views.stop_edit, name='stop_edit'),

    path('mappings/', views.mapping_list, name='mapping_list'),
    path('mappings/add/', views.mapping_create, name='mapping_create'),
    path('mappings/edit/<int:pk>/', views.mapping_edit, name='mapping_edit'),

    path('arrivals/', views.arrival_logs, name='arrival_logs'),
    path('api/update-location/', views.update_location_api, name='update_location_api'),

    path('', views.transport_home, name='transport_home'),

]

