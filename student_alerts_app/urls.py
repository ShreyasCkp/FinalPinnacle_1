from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connection

# Inline health check view
def health_check(request):
    """
    Health check endpoint to verify the application is running.
    Includes DB check.
    """
    db_status = "DOWN"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "UP"
    except Exception as e:
        db_status = f"DOWN: {str(e)}"

    return JsonResponse({
        "status": "UP",
        "database": db_status,
        "message": "Application is running"
    })

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core apps
    path('', include('master.urls')),
    path('', include('admission.urls')),
    path('', include('attendence.urls')),
    path('', include('license.urls')),
    path('', include('timetable.urls')),
    path('', include('lms.urls')),
    path('', include('core.urls')),

    # Feature apps
    path('fees/', include('fees.urls')),
    path('transport/', include('transport.urls')),
    path('hr/', include('hr.urls')),

    # Health check endpoint
    path('health/', health_check),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
