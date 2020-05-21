#!/usr/bin/env bash

#Looks trivial, but gives us a place to sed in the build hash on circle without breaking docker layer caches
GIT_HASH=$GIT_HASH

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
   #todo(COVERAGE): fix so that eth_worker is included
   coverage run invoke_tests.py
   ret=$?
   if [ "$ret" -ne 0 ]; then
     exit $ret
   fi
   bash <(curl -s https://codecov.io/bash) -cF python
else
  uwsgi --socket 0.0.0.0:9000 --protocol http  --processes 4 --enable-threads --module=server.wsgi:app --stats :3031 --stats-http
fi

