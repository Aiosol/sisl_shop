"""
Django settings for eshop_project project.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-*lj^j+jtg%l(2o_4x+6&4=h%zp%5*s5w626(2l*^mt8v&$7kjm'
DEBUG = False
ALLOWED_HOSTS = ['mitsubishifabd.com', 'www.mitsubishifabd.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',  # Optional, if using Django REST Framework
    'eshop',           # Your custom app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eshop_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'eshop' / 'templates'],  # Look for templates in eshop/templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'eshop_project.wsgi.application'

# Keep using SQLite but set the proper production settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEBUG = False
ALLOWED_HOSTS = ['mitsubishifabd.com', 'www.mitsubishifabd.com']

# Make sure static files are properly configured
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static_root'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ---------------------------------------------------------------------
# Email Configuration for Production (Google Workspace)
# ---------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'info@sisl-bd.com'
EMAIL_HOST_PASSWORD = 'YOUR_GOOGLE_WORKSPACE_APP_PASSWORD'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'info@sisl-bd.com'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'