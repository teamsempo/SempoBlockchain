#!/usr/bin/env bash

echo $CONTAINER_MODE

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

if [ "$CONTAINER_MODE" == 'TEST' ]; then
   coverage run -m pytest
   ret=$?
   if [ "$ret" -ne 0 ]; then
     exit $ret
   fi
   bash <(curl -s https://codecov.io/bash) -cF python
elif [ "$CONTAINER_MODE" == 'ETH_WORKER_TEST' ]; then
   echo pass
else
  uwsgi --socket 0.0.0.0:9000 --protocol http  --processes 4 --enable-threads --module=server.wsgi:app --stats :3031 --stats-http
fi

