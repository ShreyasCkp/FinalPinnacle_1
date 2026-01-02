import os
from django.core.wsgi import get_wsgi_application

# Check if environment variable DJANGO_ENV is set
# Use 'deployment' or 'production' for Azure, else default to local
DJANGO_ENV = os.getenv('DJANGO_ENV', 'local').lower()
settings_module = (
    'student_alerts_app.deployment'
    if DJANGO_ENV in ('deployment', 'production')
    else 'student_alerts_app.settings'
)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

application = get_wsgi_application()
