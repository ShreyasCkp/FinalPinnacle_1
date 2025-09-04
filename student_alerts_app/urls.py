from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin', admin.site.urls),
    path('', include('master.urls')), 
    path('', include('admission.urls')), # Includes app-level URLs for the routes defined in `master.urls`
    path('', include('attendence.urls')),
    path('', include('license.urls')),
    # project/urls.py
path('', include('timetable.urls')),
path('', include('timetable.urls')),
path('', include('lms.urls')),



path('', include('core.urls')),



path('fees', include('fees.urls')),
path('transport/', include('transport.urls')),
 path('hr/', include('hr.urls')),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)