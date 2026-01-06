
import os
from pathlib import Path
from urllib.parse import urlparse
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/1')

SECRET_KEY = config('SECRET_KEY', default='django-insecure-key')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0', cast=Csv())


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'channels',
    'drf_spectacular_websocket',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'corsheaders',
    'django_rq',
    'allauth',
    'allauth.account',
    'scraper',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
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

ROOT_URLCONF = 'lua_web_scrapper.urls'

WSGI_APPLICATION = 'lua_web_scrapper.wsgi.application'
ASGI_APPLICATION = 'lua_web_scrapper.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

if not DEBUG:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST'),
        'PORT': config('POSTGRES_PORT'),
    }


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


LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


def parse_redis_url(url):
    """Parse Redis URL para extrair host, port e database."""
    parsed = urlparse(url)
    return {
        'HOST': parsed.hostname or 'localhost',
        'PORT': parsed.port or 6379,
        'DB': int(parsed.path.lstrip('/')) if parsed.path else 0,
    }


redis_config = parse_redis_url(REDIS_URL)

RQ_QUEUES = {
    'default': {
        **redis_config,
        'DEFAULT_TIMEOUT': 600,
    },
    'scraping': {
        **redis_config,
        'DEFAULT_TIMEOUT': 600,
    },
    'lua_execution': {
        **redis_config,
        'DEFAULT_TIMEOUT': 300,
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default=f"{FRONTEND_URL},http://127.0.0.1:3000",
    cast=Csv()
)

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default=f"{FRONTEND_URL},http://127.0.0.1:3000",
    cast=Csv()
)

SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_AGE = 1209600  # 2 semanas em segundos
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_PATH = '/'
SESSION_COOKIE_SECURE = config(
    'SESSION_COOKIE_SECURE', default=not DEBUG, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = config('SESSION_COOKIE_SAMESITE', default='Lax')

CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_PATH = '/'
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=not DEBUG, cast=bool)
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = config('CSRF_COOKIE_SAMESITE', default='Lax')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_UNIQUE_EMAIL = True

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

LOGIN_REDIRECT_URL = '/api/auth/completed/'
ACCOUNT_LOGIN_REDIRECT_URL = LOGIN_REDIRECT_URL

ACCOUNT_LOGOUT_REDIRECT_URL = FRONTEND_URL + '/'

SITE_ID = 1

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'EXCEPTION_HANDLER': 'scraper.exceptions.handle_exception',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Lua Web Scrapper API',
    'DESCRIPTION': 'API para execução de scripts Lua com Splash para automação web',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/',
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'DEFAULT_GENERATOR_CLASS': 'drf_spectacular_websocket.schemas.WsSchemaGenerator',
    'SWAGGER_UI_SETTINGS': {
        'connectSocket': True,
        'socketMaxMessages': 8,
        'socketMessagesInitialOpened': False,
    },
    'EXTENSIONS_INFO': {
        'x-websocket': {
            'description': 'WebSocket connections for real-time notifications',
        }
    },
}
