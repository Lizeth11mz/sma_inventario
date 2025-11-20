# sma_inventario/settings.py
import os
from pathlib import Path
import pymysql

# Instala pymysql para usarlo como driver de MySQL
pymysql.install_as_MySQLdb()

# ==========================================================
# BASE DIR
# ==========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================================
# SECURITY
# ==========================================================
SECRET_KEY = 'django-insecure-z*5-1p*s'  # Cambiar en producción
DEBUG = True
ALLOWED_HOSTS = []

# ==========================================================
# APPS
# ==========================================================
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django.contrib.humanize',

    # Tus apps
    'core',
    'inventario',
    'admin_sistema',
]

# ==========================================================
# MIDDLEWARE
# ==========================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sma_inventario.urls'

# ==========================================================
# TEMPLATE SETTINGS
# ==========================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # ⚠️ IMPORTANTE: NO USAR DIRECTORIO GLOBAL SI USAS APP_DIRS
        'DIRS': [],

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

WSGI_APPLICATION = 'sma_inventario.wsgi.application'

# ==========================================================
# DATABASE (MariaDB/MySQL)
# ==========================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sma_inventario_db',
        'USER': 'root',
        'PASSWORD': 'Lizeth11',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# ==========================================================
# AUTHENTICATION
# ==========================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'

USE_I18N = True
USE_TZ = True

# ==========================================================
# STATIC FILES (IMPORTANTE PARA RECONOCER LA CARPETA 'static' EN LA RAÍZ)
# ==========================================================
# 1. Donde Django espera encontrar archivos estáticos al usar {% static '...' %}
STATIC_URL = '/static/'

# 2. Directorios adicionales donde Django debe buscar archivos estáticos.
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# 3. Directorio donde se recopilan los archivos estáticos en producción (python manage.py collectstatic)
STATIC_ROOT = BASE_DIR / "staticfiles"

# ==========================================================
# LOGIN / LOGOUT
# ==========================================================
LOGIN_REDIRECT_URL = '/inventario/dashboard/'
LOGIN_URL = 'core:login'
# ✅ CORRECCIÓN FINAL: Se usa el nombre de la vista 'core:index' para redirigir a la página principal.
LOGOUT_REDIRECT_URL = 'core:index' 

# ==========================================================
# AUTO FIELD
# ==========================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'