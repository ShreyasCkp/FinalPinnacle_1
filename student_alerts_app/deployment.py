
import os
from .settings import *
from .settings import BASE_DIR

# Allow all hosts: WEBSITE_HOSTNAME is set in Azure App Service
# Get the ALLOWED_HOSTS from environment variable, with fallback
allowed_hosts_env = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',')]

# CSRF_TRUSTED_ORIGINS is required for Azure App Service to allow CSRF protection
# CSRF stands for Cross-Site Request Forgery, a security vulnerability that allows 
# an attacker to trick a user into submitting a request that they did not intend to make.
CSRF_TRUSTED_ORIGINS = ['https://' + host for host in ALLOWED_HOSTS if host not in ['localhost', '127.0.0.1']]

# Instruct Whitenoise to skip compression for binary static files
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.webp',
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
    '.svg', '.ico', '.mp4', '.webm'
]

# DEBUG disabled for production. Because this is a production environment, 
# it is important to disable DEBUG mode to prevent sensitive information from being exposed.
DEBUG = False

# whitenoise.middleware.WhiteNoiseMiddleware : This middleware is used for serving static files in production.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
]

# Static files configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'


STATIC_ROOT = os.path.join(BASE_DIR, 'static')
import os
import sys

# Debug logs (will appear in Azure logs)
print("DB_NAME:", os.getenv('DB_NAME'), file=sys.stderr)
print("DB_USER:", os.getenv('DB_USER'), file=sys.stderr)
print("DB_PASSWORD:", os.getenv('DB_PASSWORD'), file=sys.stderr)
print("DB_HOST:", os.getenv('DB_HOST'), file=sys.stderr)

# Database configuration for Azure PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST','127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',  # Enforce secure connection
        },
    }
}