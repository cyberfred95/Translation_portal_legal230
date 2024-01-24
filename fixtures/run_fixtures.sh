#!/bin/sh

echo "LOAD FIXTURES"
python ./../manage.py loaddata ./../fixtures/languages.json
exec "$@"
