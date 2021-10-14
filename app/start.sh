#! /usr/bin/env bash
set -e

echo Container mode: $CONTAINER_MODE

cd app
echo upgrading database
python manage.py db upgrade

ret=$?
if [ "$ret" -ne 0 ]; then
  exit $ret
fi

ret=$?
if [ "$ret" -ne 0 ]; then
  exit $ret
fi

if [ "$CONTAINER_MODE" == 'TEST' ]; then
   coverage run -m pytest test_app -v
   ret=$?
   if [ "$ret" -ne 0 ]; then
     exit $ret
   fi
   if [ ! -z "$CODECOV_TOKEN" ]; then # only report if CODECOV_TOKEN is set
     curl -Os https://uploader.codecov.io/latest/linux/codecov
     chmod +x codecov
     ./codecov -t ${CODECOV_TOKEN} -F python
   fi
elif [ "$CONTAINER_MODE" == 'ETH_WORKER_TEST' ]; then
   echo pass
   sleep infinity
else

  echo upgrading dataset

  python manage.py update_data
  # Start Supervisor, with Nginx and uWSGI
  exec /usr/bin/supervisord
fi


