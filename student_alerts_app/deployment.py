import os
from decouple import config
from .settings import *

# ✅ Production mode
DEBUG = False

# ✅ Allow Azure + local + container IPs
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '169.254.133.3',  # Azure internal container IP
    'pinnacle-college-final-gwdbf8dvfcetgmef.centralindia-01.azurewebsites.net',
    '.azurewebsites.net',  # wildcard for Azure apps
]

# ✅ CSRF trusted origins (only https)
CSRF_TRUSTED_ORIGINS = [
    f"https://{host.strip()}" for host in ALLOWED_HOSTS
    if host not in ['localhost', '127.0.0.1'] and not host.startswith('.')
]

# ✅ Database (with SSL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {'sslmode': 'require'},
    }
}

# ✅ Gunicorn recommended startup command (for Azure)
# Set this in Azure → Configuration → General settings → Startup Command:
# gunicorn student_alerts_app.wsgi --timeout 120 --log-file -

# ✅ Security (optional but recommended)
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
