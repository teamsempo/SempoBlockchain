#!/usr/bin/env bash
sleep 10
echo "Running docker worker script"
if [ "$CONTAINER_MODE" = 'TEST' ]; then
  echo pass
elif [ "$CONTAINER_TYPE" == 'BEAT' ]; then
  echo "Starting Beat Worker"
  celery -A eth_manager beat --loglevel=WARNING
elif [ "$CONTAINER_TYPE" == 'FILTER' ]; then
  python ethereum_filter_test.py
elif [ "$CONTAINER_TYPE" == 'PROCESSOR' ]; then
  echo "Starting Processor Worker"
  celery -A eth_manager worker --loglevel=INFO --concurrency=4 --pool=eventlet -Q=processor
elif [ "$CONTAINER_TYPE" == 'LOW_PRIORITY_WORKER' ]; then
  echo "Starting Low Priority Worker"
  celery -A eth_manager worker --loglevel=INFO --concurrency=4 --pool=eventlet -Q=low-priority,celery
elif [ "$CONTAINER_TYPE" == 'HIGH_PRIORITY_WORKER' ]; then
  echo "Starting High Priority Worker"
  celery -A eth_manager worker --loglevel=INFO --concurrency=4 --pool=eventlet -Q=high-priority

else
  echo "Running alembic upgrade (Default)"
  alembic upgrade head

  ret=$?
  if [ "$ret" -ne 0 ]; then
    exit $ret
  fi
  echo "Starting Generic Worker (Default)"
  celery -A eth_manager worker --loglevel=INFO --concurrency=10 --pool=eventlet	
fi

#
#celery -A worker beat --loglevel=WARNING
