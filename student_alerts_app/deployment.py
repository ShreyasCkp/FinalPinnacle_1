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

# ✅ Security (optional but recommended)
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

