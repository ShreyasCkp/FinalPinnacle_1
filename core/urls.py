
from django.urls import path
from .views import recent_activity_view

urlpatterns = [
    # your other paths
    path('recent_activity', recent_activity_view, name='recent_activity_view'),
]
