#!/bin/sh

python manage.py makemigrations --no-input

# Workaround
# dbmail хранит миграции внутри контейнера.
# В новых контейнерах они создаются заново и
# конфликтуют с бд.

#bash utility/load_data.sh
#bash utility/make_pip_cache.sh

export DJANGO_SETTINGS_MODULE=legal.settings_dev
# gunicorn --bind 0.0.0.0:8099 --reload -w 5 -t 50 legal.wsgi:application

gunicorn \
  --bind 0.0.0.0:8099 \
  -w 2 \
  --worker-class gthread \
  --threads 8 \
  --timeout 120 \
  --graceful-timeout 120 \
  --keep-alive 5 \
  --access-logfile - \
  --error-logfile - \
  --log-level debug \
  legal.wsgi:application