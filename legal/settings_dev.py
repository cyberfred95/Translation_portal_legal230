from .settings import *

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
