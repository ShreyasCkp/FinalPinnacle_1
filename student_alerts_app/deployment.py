import os
from decouple import config
from .settings import *

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='college-portal-efdhgwg8eqg0ejaj.centralindia-01.azurewebsites.net').split(',')

CSRF_TRUSTED_ORIGINS = [
    f"https://{host}" for host in ALLOWED_HOSTS if host not in ['localhost', '127.0.0.1']
]

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

# Whitenoise already set in base settings
