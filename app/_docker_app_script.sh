#!/usr/bin/env sh

cd src
echo upgrading database
python manage.py db upgrade
echo upgrading dataset
python manage.py update_data

if [ "$CONTAINER_MODE" = 'TEST' ]; then
  python invoke_tests.py
else
  uwsgi --socket 0.0.0.0:9000 --protocol http  --processes 4 --enable-threads --module=server.wsgi:app
fi

