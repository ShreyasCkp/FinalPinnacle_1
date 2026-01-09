import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

DJANGO_ENV = os.getenv('DJANGO_ENV', 'local').lower()
ENV_FILE = '.env.production' if DJANGO_ENV in ('deployment', 'production') else '.env.local'
ENV_PATH = BASE_DIR / ENV_FILE
FALLBACK_ENV_PATH = BASE_DIR / '.env'


def _load_env_file(path):
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file(ENV_PATH)
if ENV_PATH != FALLBACK_ENV_PATH:
    _load_env_file(FALLBACK_ENV_PATH)

SECRET_KEY = config('SECRET_KEY', default='fallback_secret_key')
DEBUG = config('DEBUG', default=True, cast=bool)
PUBLIC_ACCESS = config('PUBLIC_ACCESS', default=False, cast=bool)
# ALLOWED_HOSTS - handle both comma-separated string and wildcard
allowed_hosts_str = config('ALLOWED_HOSTS', default='*')
ALLOWED_HOSTS = ['*'] if allowed_hosts_str == '*' else [h.strip() for h in allowed_hosts_str.split(',')]

# Installed apps
INSTALLED_APPS = [
    'master', 'admission', 'license', 'attendence', 'timetable', 'lms',
    'core', 'fees', 'transport', 'hr',
    'django.contrib.admin', 'django.contrib.auth',
    'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.messages', 'django.contrib.staticfiles',
    'student_alerts_app',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'license.middleware.check_license.LicenseCheckMiddleware',
]


ROOT_URLCONF = 'student_alerts_app.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'student_alerts_app' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'master.context_processors.user_form_permissions',
                'lms.context_processors.student_context',
                'lms.context_processors.employee_context',
                'lms.context_processors.parent_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'student_alerts_app.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

# Static / Media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Whitenoise skip compress for binaries
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.webp',
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
    '.svg', '.ico', '.mp4', '.webm'
]

# Site URL Configuration
SITE_URL = config('SITE_URL', default='http://localhost:8000')
LOGIN_URL = config('LOGIN_URL', default=f'{SITE_URL}/admission/student-login/')

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

# Email Provider Configuration (for Postmark/SendGrid)
EMAIL_PROVIDER_NAME = config('EMAIL_PROVIDER_NAME', default='smtp')
EMAIL_PROVIDERS = {
    'smtp': {
        'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
    },
    'postmark': {
        'API_TOKEN': config('POSTMARK_API_TOKEN', default=''),
        'FROM_EMAIL': config('POSTMARK_FROM_EMAIL', default=DEFAULT_FROM_EMAIL),
    },
    'sendgrid': {
        'API_TOKEN': config('SENDGRID_API_KEY', default=''),
        'FROM_EMAIL': config('SENDGRID_FROM_EMAIL', default=DEFAULT_FROM_EMAIL),
    },
}

# Msgkart
MSGKART_API_KEY = config('MSGKART_API_KEY', default='')
MSGKART_EMAIL = config('MSGKART_EMAIL', default='')
MSGKART_PHONE_ID = config('MSGKART_PHONE_ID', default='')
MSGKART_ACCOUNT_ID = config('MSGKART_ACCOUNT_ID', default='')
MSGKART_BASE_URL = config('MSGKART_BASE_URL', default='https://api.msgkart.com')

# CSRF Configuration
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000'
).split(',')

# Timezone
TIME_ZONE = config('TIME_ZONE', default='Asia/Kolkata')
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
