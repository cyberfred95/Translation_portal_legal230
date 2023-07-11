#!/bin/sh

python manage.py makemigrations --no-input

# Workaround
# dbmail хранит миграции внутри контейнера.
# В новых контейнерах они создаются заново и
# конфликтуют с бд.
if ! python manage.py migrate --no-input; then
    python manage.py migrate --no-input --fake dbmail
    python manage.py migrate --no-input
fi

#bash utility/load_data.sh
#bash utility/make_pip_cache.sh

python manage.py runserver --settings=legal.settings 0.0.0.0:8000
