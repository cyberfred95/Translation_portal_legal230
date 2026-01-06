import sys
import os
from pathlib import Path

from celery.schedules import crontab
from django.utils.translation import gettext_lazy as _

# ============================================================================
# Base paths & environment loading
# ============================================================================
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Manually load environment variables from the .env file

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

# ============================================================================
# Security / core
# ============================================================================
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes', 'on')
SECRET_KEY = os.environ.get('SECRET_KEY')

# ALLOWED_HOSTS from environment variable
ALLOWED_HOSTS_STR = os.environ.get('ALLOWED_HOSTS')

if ALLOWED_HOSTS_STR:
    # Parse format: [host1, host2, host3] or host1,host2,host3
    if ALLOWED_HOSTS_STR.startswith('[') and ALLOWED_HOSTS_STR.endswith(']'):
        # Remove brackets and parse
        hosts_str = ALLOWED_HOSTS_STR[1:-1]
        ALLOWED_HOSTS = [host.strip().strip("'\"") for host in hosts_str.split(',') if host.strip()]
    else:
        # Fallback to comma-separated format
        ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(',') if host.strip()]

# Proxy / headers
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ============================================================================
# Django apps, middleware, URLs, templates
# ============================================================================
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
    # 'compressor',  # archived: not used
    'django_filters',
    'rosetta',
    'django_cleanup.apps.CleanupConfig',
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
    # 'compressor.finders.CompressorFinder',  # archived: not used
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

ROOT_URLCONF = 'legal.urls'
WSGI_APPLICATION = 'legal.wsgi.application'

# ============================================================================
# Authentication / accounts
# ============================================================================
ACCOUNT_ADAPTER = 'core.account_adapter.NoNewUsersAccountAdapter'
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = 'none'

LOGIN_URL = '/users/login/'
LOGOUT_REDIRECT_URL = "/users/login/"
LOGIN_REDIRECT_URL = '/'

# ============================================================================
# Internationalization / localization
# ============================================================================
LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', _('English')),
    ('fr', _('French')),
)
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [ BASE_DIR / 'locale/', ]

# ============================================================================
# Static & media files
# ============================================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    os.path.join(BASE_DIR, "templates", "static"),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'static_collected')

if not DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Compression (archived: not used)
# COMPRESS_ENABLED = True
# COMPRESS_OFFLINE = False

# ============================================================================
# Database
# ============================================================================
# Detect if we are in test mode
TESTING = 'test' in sys.argv

if TESTING:
    # SQLite configuration used only for tests (fast, no external deps)
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
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# ============================================================================
# Caching
# ============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ============================================================================
# Celery / Redis
# ============================================================================
# (REDIS_HOST/REDIS_PORT were not directly used)
# REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
# REDIS_PORT = os.environ.get("REDIS_PORT", "6379")

CELERY_BROKER_URL = os.environ.get("CELERY_REDIS", "redis://redis:6379")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_REDIS", "redis://redis:6379")
CELERY_BROKER_TRANSPORT = "redis"  # Force Redis transport
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_ALWAYS_EAGER = bool(os.environ.get("CELERY_ALWAYS_EAGER", False))
CELERY_BEAT_SCHEDULE = {
    'process_daily_subscription_renewals': {
        'task': 'subscriptions.tasks.process_daily_subscription_renewals',
        'schedule': crontab(minute="0", hour="0")
    },
    'report_daily_metered_usage': {
        'task': 'subscriptions.tasks.report_daily_metered_usage',
        'schedule': crontab(minute="5", hour="0")
    }
}

# ============================================================================
# Stripe Metering
# ============================================================================
STRIPE_METER_EVENT_NAME = os.environ.get('STRIPE_METER_EVENT_NAME', 'apinbchar_standard')

# ============================================================================
# Logging
# ============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
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
        'users': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================================
# Application-specific settings
# ============================================================================
AUTH_USER_MODEL = 'users.User'
ROSETTA_SHOW_AT_ADMIN_PANEL = True

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# LARA Translation API Configuration
LARA_API_URL = os.environ.get('LARA_API_URL')
LARA_ACCESS_KEY_ID = os.environ.get('LARA_ACCESS_KEY_ID')
LARA_ACCESS_KEY_SECRET = os.environ.get('LARA_ACCESS_KEY_SECRET')

# Cloud Storage API Configuration - DÉSACTIVÉ
# CLOUDSTORAGE_API_URL = os.environ.get('CLOUDSTORAGE_API_URL')
# CLOUDSTORAGE_API_KEY = os.environ.get('CLOUDSTORAGE_API_KEY')

# Email Configuration
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
QUOTE_CC_EMAIL = os.environ.get('QUOTE_CC_EMAIL')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL')
MINIMUM_QUOTE_AMOUNT = float(os.environ.get('MINIMUM_QUOTE_AMOUNT', '0'))

# Stripe Configuration
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
STRIPE_PORTAL_RETURN_URL = "https://portail.lexamt.fr/fr/profile-details/"
STRIPE_CHECKOUT_SUCCESS_URL = "https://portail.lexamt.fr"
STRIPE_CHECKOUT_CANCEL_URL = "https://portail.lexamt.fr"

# Active Trail Configuration
ACTIVE_TRAIL_SENDING_PROFILE_ID = int(
    os.environ.get('ACTIVE_TRAIL_SENDING_PROFILE_ID', 0))
ACTIVE_TRAIL_USER_PROFILE_FROMNAME = os.environ.get(
    'ACTIVE_TRAIL_USER_PROFILE_FROMNAME')
ACTIVE_TRAIL_SEND_EMAIL_REQUEST_URL = 'https://webapi.mymarketing.co.il/api/OperationalMessage/Message'
ACTIVE_TRAIL_API_KEY = os.environ.get('ACTIVE_TRAIL_API_KEY')

# Adobe PDF Services Configuration
ADOBE_CLIENT_ID = os.environ.get('ADOBE_CLIENT_ID')
ADOBE_CLIENT_SECRET = os.environ.get('ADOBE_CLIENT_SECRET')
ADOBE_ORGANIZATION_ID = os.environ.get('ADOBE_ORGANIZATION_ID')


