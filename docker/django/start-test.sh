#!/bin/sh

while [ ! -f /home/django/app/static/builded.txt ]
do
    echo "wait node compile..."
    sleep 10
done

# sh utility/make_pip_cache.sh

# need for dbmail
# python manage.py makemigrations --no-input
# python manage.py migrate --no-input
# python manage.py createinitialfieldhistory
python manage.py compress --force
python manage.py collectstatic --noinput
python manage.py test
