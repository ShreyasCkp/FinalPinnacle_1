import os
from decouple import config
from .settings import *

# ✅ Production mode
DEBUG = False


APPEND_SLASH = True

# ✅ Allow Azure + local + container IPs
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',') if config('ALLOWED_HOSTS', default='*') != '*' else ['*']

# ✅ CSRF trusted origins (from environment variable)
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://pinnacle-college-final-gwdbf8dvfcetgmef.centralindia-01.azurewebsites.net'
).split(',')
# ✅ Database (with SSL for Azure)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {'sslmode': 'require'},
    }
}

# ✅ Gunicorn recommended startup command (for Azure)
# Set this in Azure → Configuration → General settings → Startup Command:
# gunicorn student_alerts_app.wsgi --timeout 120 --log-file -
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Security settings

SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Use X-Forwarded-Proto header so Django knows HTTPS is already used
# Timezone and localization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_L10N = True
USE_TZ = True
