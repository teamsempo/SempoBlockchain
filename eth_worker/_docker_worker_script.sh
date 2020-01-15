#!/usr/bin/env bash
sleep 10

if [ "$CONTAINER_MODE" = 'TEST' ]; then
  echo pass
elif [ "$CONTAINER_TYPE" == 'BEAT' ]; then
  celery -A eth_manager beat --loglevel=WARNING
elif [ "$CONTAINER_TYPE" == 'FILTER' ]; then
  python ethereum_filter_test.py
elif [ "$CONTAINER_TYPE" == 'PROCESSOR' ]; then
  celery -A eth_manager worker --loglevel=INFO --concurrency=4 --pool=eventlet -Q=processor
else
  alembic upgrade head

  ret=$?
  if [ "$ret" -ne 0 ]; then
    exit $ret
  fi

  celery -A eth_manager worker --loglevel=INFO --concurrency=10 --pool=eventlet
fi

#
#celery -A worker beat --loglevel=WARNING
