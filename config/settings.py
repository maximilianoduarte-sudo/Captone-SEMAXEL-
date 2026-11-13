"""
Django settings for the "Sistema de Gestión de Mantenimiento" project.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde el archivo .env (ubicado en la raíz del proyecto).
load_dotenv(BASE_DIR / '.env')


# Sin valor por defecto: arrancar con una clave conocida firmaría sesiones y
# tokens CSRF con material público del repositorio.
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured(
        'Falta SECRET_KEY en el entorno. Defínela en el archivo .env '
        '(ver .env.example) antes de iniciar la aplicación.'
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# Application definition

INSTALLED_APPS = [
    # Admin con alcance por rol (accounts.admin_site.SEMAXELAdminSite)
    'accounts.admin_site.SEMAXELAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # API REST para la app móvil del técnico
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    # Aplicaciones del sistema
    'accounts',
    'empresas',
    'sucursales',
    'tecnicos',
    'tickets',
    'ofertas',
    'sla',
    'mantenimiento',
    'dashboard',
    'api',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.usuario_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'capstone_semaxel'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # Rechaza contraseñas parecidas a los datos del usuario.
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    # Longitud mínima exigida por el sistema.
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    # Rechaza contraseñas comunes y demasiado simples.
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    # Exige mayúscula, número y símbolo (accounts.validators).
    {
        'NAME': 'accounts.validators.ComplejidadPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


# Media files (imágenes y archivos subidos)

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Autenticación
# Redirige al login cuando una vista exige usuario autenticado.
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'


# API REST (app móvil del técnico)
# La app se autentica con un token en la cabecera "Authorization: Token <clave>".
# No usa la sesión del navegador, así que la API no depende de cookies ni CSRF.
# Por defecto toda operación exige un usuario autenticado y responde solo JSON.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # Documentación OpenAPI generada desde el código (drf-spectacular).
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'SEMAXEL · API de la app móvil del técnico',
    'DESCRIPTION': (
        'API REST que usa la app Android del técnico de terreno.\n\n'
        'Autenticación: `POST /api/v1/auth/login/` entrega un token; las demás '
        'operaciones exigen la cabecera `Authorization: Token <token>`. '
        'En esta página: botón **Authorize** y escribir `Token ` seguido del token.\n\n'
        'Errores: 400 datos inválidos (un mensaje por campo), 401 sin token o '
        'token inválido, 403 no es un técnico habilitado, 404 no existe o no le '
        'corresponde, 409 una regla de negocio no lo permite (el cuerpo trae '
        '`detail` y `codigo`).'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # El esquema y Swagger UI son públicos: describen la API, no muestran datos.
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': [],
    'COMPONENT_SPLIT_REQUEST': True,
}

# Reglas de la app móvil
# Distancia máxima (en metros) entre el técnico y la sucursal para dar por
# verificada su llegada con GPS.
SEMAXEL_RADIO_LLEGADA_METROS = int(os.environ.get('SEMAXEL_RADIO_LLEGADA_METROS', '150'))
# Fotos de evidencia: máximo por orden y tamaño máximo por archivo.
SEMAXEL_MAX_EVIDENCIAS_POR_ORDEN = 10
SEMAXEL_MAX_TAMANO_IMAGEN_MB = 8

# Notificaciones push. "consola" solo las escribe en el log (desarrollo);
# "fcm" las envía con Firebase Cloud Messaging y exige FCM_CREDENTIALS_FILE
# (archivo JSON de la cuenta de servicio de Firebase) y el paquete google-auth.
SEMAXEL_PUSH_BACKEND = os.environ.get('SEMAXEL_PUSH_BACKEND', 'consola')
FCM_CREDENTIALS_FILE = os.environ.get('FCM_CREDENTIALS_FILE', '')
