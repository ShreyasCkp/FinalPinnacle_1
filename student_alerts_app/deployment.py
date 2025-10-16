"""
Deployment-specific settings for Azure App Service.
"""
import os
from .settings import *
from .settings import BASE_DIR

# Override ALLOWED_HOSTS from environment variable
allowed_hosts_env = os.getenv('ALLOWED_HOSTS', 'Pinnacle-College-Final.azurewebsites.net,localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',')]

# CSRF_TRUSTED_ORIGINS for Azure
CSRF_TRUSTED_ORIGINS = ['https://' + host for host in ALLOWED_HOSTS if host not in ['localhost', '127.0.0.1']]

# Whitenoise: Skip compression for binary files
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.webp',
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
    '.svg', '.ico', '.mp4', '.webm'
]

# Database configuration for Azure PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'institute_db_pg'),
        'USER': os.getenv('DB_USER', 'dbadmin'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'Admin@2025'),
        'HOST': os.getenv('DB_HOST', 'collegepgdb2025.postgres.database.azure.com'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}
