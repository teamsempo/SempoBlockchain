#!/usr/bin/env bash
echo Container mode: $CONTAINER_MODE

cd src
ret=$?
if [ "$ret" -ne 0 ]; then
  exit $ret
fi

ret=$?
if [ "$ret" -ne 0 ]; then
  exit $ret
fi

if [ "$CONTAINER_MODE" == 'TEST' ]; then
   coverage run -m pytest test_app -x -v
   ret=$?
   if [ "$ret" -ne 0 ]; then
     exit $ret
   fi
   if [ ! -z "$CODECOV_TOKEN" ]; then # only report if CODECOV_TOKEN is set
     bash <(curl -s https://codecov.io/bash) -cF python
   fi
elif [ "$CONTAINER_MODE" == 'ETH_WORKER_TEST' ]; then
   echo pass
   sleep infinity
elif [ "$CONTAINER_MODE" == 'BOOTSTRAP' ]; then
  echo upgrading database
  echo bootstrapping dataset
  python manage.py db upgrade
  python manage.py update_data
else
  uwsgi --socket 0.0.0.0:9000 --protocol http  --processes 4 --enable-threads --module=server.wsgi:app --stats :3031 --stats-http
fi

