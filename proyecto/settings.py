"""
Django settings for proyecto project.
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-rog-af+&wv-4hgeofrrhb7*(u^r5g03y78e367=mnf107r_8+='

DEBUG = True
ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'clientes',
    'archivos',
    'Materiales',
    'Muebles',
    'Ventas',
    'Sucursales',
    'Empleados',
    'Compras',
    'Parametros',
    'Trabajo',
    'Notificaciones',
    'nested_admin',
]

JAZZMIN_SETTINGS = {
    "site_title": "MSJ Admin",
    "site_header": "Panel Administrador",
    "site_brand": "Panel Administrador",
    "welcome_sign": "Iniciar sesión",
    
    # Configuración de idioma CRUCIAL
    "language": "es",
    "default_language": "es",
    
    # Configuraciones adicionales para forzar español
    "show_ui_builder": False,
    "related_modal_active": True,
    "order_with_respect_to": [
    "Materiales.Materiale",
    "Materiales.Proveedore",
    "Materiales.CategoriasMateriale",
    "Muebles.Mueble",
    "Muebles.CategoriasMueble",
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "clientes.cliente": "fas fa-user",
        "clientes.documentoscliente": "fa-solid fa-file", 
        "archivos.documento": "fa-solid fa-file-lines", 
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "Muebles.Mueble":"fa-solid fa-couch",
        "Muebles.Tamaño": "fa-solid fa-ruler",
        "Materiales.materiale":"fa-solid fa-layer-group",
        "Materiales.CategoriasMateriale":"fa-solid fa-list",
        "Materiales.Proveedore":"fa-solid fa-user-tag",
        "Muebles.CategoriasMueble":"fa-solid fa-list",
        "Materiales.UnidadesMedida":"fa-solid fa-compass-drafting",
        "Muebles.MuebleMateriale":"fa-solid fa-layer-group",
        "Sucursales.Sucursale":"fa-solid fa-store",
        "Ventas.OrdenesVenta":"fa-solid fa-dollar-sign",
        "Empleados.Empleado":"fa-solid fa-user-tie",
        
    },
    

}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Este debe estar aquí
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'proyecto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.i18n',  # AÑADE ESTE
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'builtins': [  # OPCIONAL: ayuda con traducciones
                'django.templatetags.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'proyecto.wsgi.application'

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

# Internationalization - SECCIÓN MÁS IMPORTANTE
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Tegucigalpa'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Configuración de idiomas EXPLÍCITA
LANGUAGES = [
    ('es', 'Spanish'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files
# settings.py
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
if DEBUG:#importante para los iframes
    X_FRAME_OPTIONS = 'ALLOWALL'