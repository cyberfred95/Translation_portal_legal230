import sys
import os
from pathlib import Path

from celery.schedules import crontab
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Charger manuellement les variables d'environnement depuis le fichier .env


def load_env_file():
    env_file = os.path.join(BASE_DIR, '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    os.environ.setdefault(key.strip(), value.strip())


load_env_file()

SECRET_KEY = os.environ.get('SECRET_KEY')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '0.0.0.0', 'legal230.portal.custom.mt', '141.145.204.44', 'portail.lexamt.fr', 'portail.lexamt.com',
                 'portail.lexamt.tech', '89.168.44.123', 'test.portail.lexamt.fr', 'test.portail.lexamt.com', 'test.portail.lexamt.tech',
                 'api.portail.lexamt.fr', 'api.portail.lexamt.com','141.253.120.134']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'legal.apps.LegalConfig',
    'rest_framework',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.sites',
    'allauth',
    'compressor',
    'django_filters',
    'rosetta',
    'django_cleanup.apps.CleanupConfig',
    'settings.apps.SettingsConfig',
    'preferences',
    'users.apps.UsersConfig',
    'languages.apps.LanguagesConfig',
    'domains.apps.DomainsConfig',
    'stats.apps.StatsConfig',
    'glossaries.apps.GlossariesConfig',
    'writing.apps.WritingConfig',
    'subscriptions.apps.SubscriptionsConfig',
    'quoting.apps.QuotingConfig',
    'stripe_webhooks',
    'emails',
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'users.middlewares.DisableCRSFValidation',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'legal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'preferences.context_processors.preferences_cp',

            ],
        },
    },
]

WSGI_APPLICATION = 'legal.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

# Detect if we are in test mode
TESTING = 'test' in sys.argv

if TESTING:
    # SQLite configuration for tests (faster and no dependencies)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    # PostgreSQL configuration for development/production
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'legal',
            'USER': 'legal',
            'PASSWORD': 'datasvitend',
            'HOST': 'postgres',
            'PORT': '5432',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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

ACCOUNT_ADAPTER = 'core.account_adapter.NoNewUsersAccountAdapter'

SITE_ID = 1

ACCOUNT_EMAIL_VERIFICATION = 'none'

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', _('English')),
    ('fr', _('French')),
)

TIME_ZONE = 'Etc/GMT-3'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / 'locale/',
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static")
]
STATIC_ROOT = os.path.join(BASE_DIR, 'static_collected')

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = False

LOGIN_URL = '/users/login/'
LOGOUT_REDIRECT_URL = "/users/login/"
LOGIN_REDIRECT_URL = '/'

DEV_MODE = True

# Указываем в часах
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Host for sending e-mail.
EMAIL_HOST = ''

# Port for sending e-mail.
EMAIL_PORT = 465

# Optional SMTP authentication information for EMAIL_HOST.
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = True

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")

# Celery
CELERY_BROKER_URL = os.environ.get("CELERY_REDIS", "redis://redis:6379")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_REDIS", "redis://redis:6379")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_ALWAYS_EAGER = bool(os.environ.get("CELERY_ALWAYS_EAGER", False))
CELERY_BEAT_SCHEDULE = {
    'update_domains': {
        'task': 'domains.tasks.update_domains',
        'schedule': crontab(minute="0", hour="0")
    },
    'update_prompts': {
        'task': 'writing.tasks.refresh_prompts',
        'schedule': crontab(minute="0", hour="0")
    },
    'process_daily_subscription_renewals': {
        'task': 'subscriptions.tasks.process_daily_subscription_renewals',
        'schedule': crontab(minute="0", hour="0")
    }
}

OPENAI_GPT_API_KEY = os.environ.get('OPENAI_GPT_API_KEY')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

AUTH_USER_MODEL = 'users.User'

ROSETTA_SHOW_AT_ADMIN_PANEL = True

FILES_PROCESSING_API_URL = 'https://office.fileprocessing.custom.mt'

# PDF Conversion method: 'custommt' or 'adobe'
CONVERSION_METHOD = os.environ.get('CONVERSION_METHOD', 'custommt')

# Adobe PDF Services configuration
ADOBE_CLIENT_ID = os.environ.get('ADOBE_CLIENT_ID')
ADOBE_CLIENT_SECRET = os.environ.get('ADOBE_CLIENT_SECRET')
ADOBE_ORGANIZATION_ID = os.environ.get('ADOBE_ORGANIZATION_ID')


# Add logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/tmp/django_debug.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'glossaries': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'stats': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'stats.calculator': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

GLOSSARY_SYSTEM = os.environ.get("GLOSSARY_SYSTEM")
GLOSSARY_API_KEY = os.environ.get("GLOSSARY_API_KEY")

# Stripe Configuration
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
STRIPE_PORTAL_RETURN_URL = "https://portail.lexamt.fr/fr/profile-details/"

# Active Trail Configuration
ACTIVE_TRAIL_SENDING_PROFILE_ID = int(
    os.environ.get('ACTIVE_TRAIL_SENDING_PROFILE_ID', 0))
ACTIVE_TRAIL_USER_PROFILE_FROMNAME = os.environ.get(
    'ACTIVE_TRAIL_USER_PROFILE_FROMNAME')
ACTIVE_TRAIL_SEND_EMAIL_REQUEST_URL = 'https://webapi.mymarketing.co.il/api/OperationalMessage/Message'
ACTIVE_TRAIL_API_KEY = os.environ.get('ACTIVE_TRAIL_API_KEY')


