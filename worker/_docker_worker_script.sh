#!/usr/bin/env bash
echo different3

if [ "$CONTAINER_TYPE" == 'FLOWER' ]; then
  sleep 10
  flower -A worker --port=5555
elif [ "$CONTAINER_TYPE" == 'BEAT' ]; then
  celery -A worker beat --loglevel=WARNING
elif [ "$CONTAINER_TYPE" == 'FILTER' ]; then
  python ethereum_filter_test.py
else
  celery -A worker worker --loglevel=INFO --concurrency=500 --pool=eventlet
fi

#
#celery -A worker beat --loglevel=WARNING
