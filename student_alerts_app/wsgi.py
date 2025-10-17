import os
from django.core.wsgi import get_wsgi_application

# Check if environment variable DJANGO_ENV is set
# Use 'deployment' for Azure, else default to local
DJANGO_ENV = os.getenv('DJANGO_ENV', 'local').lower()

if DJANGO_ENV == 'deployment':
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        'student_alerts_app.settings.deployment'
    )
else:
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        'student_alerts_app.settings'
    )

application = get_wsgi_application()
