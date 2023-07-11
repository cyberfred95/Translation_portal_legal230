all:
	docker-compose build

start:
	docker-compose up

stop:
	docker-compose stop

runserver:
	docker-compose up runserver

shell:
	docker-compose run --rm shell /bin/bash

load_fixtures:
	python manage.py clear_language_model
	chmod 775 fixtures/run_fixtures.sh
	fixtures/run_fixtures.sh
