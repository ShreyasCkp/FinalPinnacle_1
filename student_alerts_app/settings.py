"""
Django settings for student_alerts_app project.

Based on 'django-admin startproject' using Django 2.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import posixpath


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '6e470ba8-802a-428f-b168-40d4eadee009'
 
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True




ALLOWED_HOSTS = [
    '192.168.10.221', 'localhost', '127.0.0.1',
    '122.166.213.68',
    'pinnacle-college-final-gwdbf8dvfcetgmef.centralindia-01.azurewebsites.net'
]


# Application references
# https://docs.djangoproject.com/en/2.1/ref/settings/#std:setting-INSTALLED_APPS
INSTALLED_APPS = [
    'master',
    'admission',
    'license',
    'attendence',
    'timetable',
    # Add your apps here to enable them
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

# Middleware framework
# https://docs.djangoproject.com/en/2.1/topics/http/middleware/
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'license.middleware.check_license.LicenseCheckMiddleware',
]

ROOT_URLCONF = 'student_alerts_app.urls'

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
    

# Template configuration
# https://docs.djangoproject.com/en/2.1/topics/templates/
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'student_alerts_app','templates')], 
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
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'institute_db_pg'),
        'USER': os.getenv('DB_USER', 'dbadmin'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'Admin@2025'),
        'HOST': os.getenv('DB_HOST', 'collegepgdb2025.postgres.database.azure.com'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',  # 🔐 Required for Azure PostgreSQL
        },
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/2.1/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
# settings.py

LOGIN_REDIRECT_URL = 'license_check_view'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



import os

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

TIME_ZONE = 'Asia/Kolkata'
USE_TZ = True





MSGKART_API_KEY = "3652fa38504b4d018052987ff493ea6e"
MSGKART_EMAIL = "pscm@ckpsoftware.com"
MSGKART_PHONE_ID = "677200268805951"
MSGKART_ACCOUNT_ID = "1079493607572130"
MSGKART_BASE_URL = "https://alb-backend.msgkart.com"




EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'saishashank0143@gmail.com'
EMAIL_HOST_PASSWORD = 'umht bsic hycy pgli'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER



