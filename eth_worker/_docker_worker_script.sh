#!/usr/bin/env bash
sleep 5

WORKER_CONCURRENCY=4

echo "Running alembic upgrade (Default)"
alembic upgrade head
ret=$?
if [ "$ret" -ne 0 ]; then
  exit $ret
fi
echo "Starting Generic Worker (Default)"
celery -A eth_manager worker --loglevel=DEBUG --concurrency=10 --pool=eventlet -Q=low-priority,celery,high-priority --without-gossip --without-mingle



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
  celery -A eth_manager worker --loglevel=DEBUG --concurrency=$WORKER_CONCURRENCY --pool=eventlet -Q=processor --without-gossip --without-mingle
elif [ "$CONTAINER_TYPE" == 'LOW_PRIORITY_WORKER' ]; then
  echo "Starting Low Priority Worker"
  celery -A eth_manager worker --loglevel=DEBUG --concurrency=$WORKER_CONCURRENCY --pool=eventlet -Q=low-priority,celery --without-gossip --without-mingle
elif [ "$CONTAINER_TYPE" == 'HIGH_PRIORITY_WORKER' ]; then
  echo "Starting High Priority Worker"
  celery -A eth_manager worker --loglevel=DEBUG --concurrency=$WORKER_CONCURRENCY --pool=eventlet -Q=high-priority --without-gossip --without-mingle
elif [ "$CONTAINER_TYPE" == 'FLOWER' ]; then
  flower -A worker --port=5555
elif [ "$CONTAINER_TYPE" == 'ANY_PRIORITY_WORKER' ]; then
  echo "Starting Any Priority Worker"
  celery -A eth_manager worker --loglevel=DEBUG --concurrency=$WORKER_CONCURRENCY --pool=eventlet -Q=high-priority --without-gossip --without-mingle

else
  echo "Running alembic upgrade (Default)"
  alembic upgrade head

  ret=$?
  if [ "$ret" -ne 0 ]; then
    exit $ret
  fi
  echo "Starting Generic Worker (Default)"
  celery -A eth_manager worker --loglevel=DEBUG --concurrency=10 --pool=eventlet -Q=low-priority,celery,high-priority --without-gossip --without-mingle
fi

#
#celery -A worker beat --loglevel=WARNING
