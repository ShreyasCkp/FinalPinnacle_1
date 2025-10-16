"""
Django settings for student_alerts_app project.
...
"""
import os
import posixpath

# Build paths inside the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', '6e470ba8-802a-428f-b168-40d4eadee009')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False  # Changed to False for production

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'Pinnacle-College-Final.azurewebsites.net',  # Correct Azure hostname
]

# Application definition
INSTALLED_APPS = [
    'master',
    'admission',
    'license',
    'attendence',
    'timetable',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'student_alerts_app',
    'core',
    'fees',
    'transport',
    'lms',
    'hr',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Moved from deployment.py
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'license.middleware.check_license.LicenseCheckMiddleware',
]

ROOT_URLCONF = 'student_alerts_app.urls'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'student_alerts_app', 'templates')],
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

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOGIN_REDIRECT_URL = 'license_check_view'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Consistent with Whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'  # Moved from deployment.py

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'saishashank0143@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'umht bsic hycy pgli')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Msgkart settings
MSGKART_API_KEY = os.getenv('MSGKART_API_KEY', '3652fa38504b4d018052987ff493ea6e')
MSGKART_EMAIL = os.getenv('MSGKART_EMAIL', 'pscm@ckpsoftware.com')
MSGKART_PHONE_ID = os.getenv('MSGKART_PHONE_ID', '677200268805951')
MSGKART_ACCOUNT_ID = os.getenv('MSGKART_ACCOUNT_ID', '1079493607572130')
MSGKART_BASE_URL = os.getenv('MSGKART_BASE_URL', 'https://alb-backend.msgkart.com')
