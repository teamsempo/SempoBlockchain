#!/usr/bin/env bash
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
     bash <(curl -s https://codecov.io/bash) -cF python
   fi
elif [ "$CONTAINER_MODE" == 'ETH_WORKER_TEST' ]; then
   echo pass
   sleep infinity
else

  echo upgrading dataset

  python manage.py update_data

fi

