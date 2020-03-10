#!/usr/bin/env sh
sleep 60

cd src
echo upgrading database
python manage.py db upgrade

ret=$?
if [ "$ret" -ne 0 ]; then
  exit $ret
fi

echo upgrading dataset
python manage.py update_data

ret=$?
if [ "$ret" -ne 0 ]; then
  exit $ret
fi

if [ "$CONTAINER_MODE" = 'TEST' ]; then
  python invoke_tests.py
else
  uwsgi --socket 0.0.0.0:9000 --protocol http  --processes 4 --enable-threads --module=server.wsgi:app
fi

