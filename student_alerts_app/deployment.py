import os
from decouple import config
from .settings import *

# ✅ Production mode
DEBUG = False

# ✅ Allow Azure + local + container IPs
ALLOWED_HOSTS = ['*']

# ✅ CSRF trusted origins (only https)
CSRF_TRUSTED_ORIGINS = [
    'https://pinnacle-college-final-gwdbf8dvfcetgmef.centralindia-01.azurewebsites.net',
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
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Security settings

SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Use X-Forwarded-Proto header so Django knows HTTPS is already used
