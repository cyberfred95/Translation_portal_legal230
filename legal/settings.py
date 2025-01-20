import os
from pathlib import Path

from celery.schedules import crontab
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'tyjpz-hu3tt6!9u6)g&pf4r%9)d-o3%ggxz0!&)b8gc0k_v3g0'


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '0.0.0.0', 'legal230.portal.custom.mt']


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
    'django.middleware.csrf.CsrfViewMiddleware',
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
                'preferences.context_processors.preferences_cp',

            ],
        },
    },
]

WSGI_APPLICATION = 'legal.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

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


LOGIN_URL = '/accounts/login/'
LOGOUT_REDIRECT_URL = "/accounts/login/"
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
    'update_domains':{
        'task': 'domains.tasks.update_domains',
        'schedule': crontab(minute="0", hour="0")
    },
    'update_prompts': {
        'task': 'writing.tasks.refresh_prompts',
        'schedule': crontab(minute="0", hour="0")
    }
}

OPENAI_GPT_API_KEY = 'REMOVED_OPENAI_KEY_1'
SENDGRID_API_KEY = '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'

AUTH_USER_MODEL = 'users.User'

ROSETTA_SHOW_AT_ADMIN_PANEL = True

FILES_PROCESSING_API_URL = 'https://office.fileprocessing.custom.mt'


USE_X_FORWARDED_HOST=True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
