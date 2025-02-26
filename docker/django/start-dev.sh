#!/bin/sh

python manage.py makemigrations --no-input

# Workaround
# dbmail хранит миграции внутри контейнера.
# В новых контейнерах они создаются заново и
# конфликтуют с бд.

#bash utility/load_data.sh
#bash utility/make_pip_cache.sh

python manage.py runserver --settings=legal.settings_dev 0.0.0.0:8000
