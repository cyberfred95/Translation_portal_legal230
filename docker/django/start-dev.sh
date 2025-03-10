#!/bin/sh

python manage.py makemigrations --no-input

# Workaround
# dbmail хранит миграции внутри контейнера.
# В новых контейнерах они создаются заново и
# конфликтуют с бд.

#bash utility/load_data.sh
#bash utility/make_pip_cache.sh

export DJANGO_SETTINGS_MODULE=legal.settings_dev
gunicorn --bind 0.0.0.0:8099 --reload -w 5 -t 50 legal.wsgi:application