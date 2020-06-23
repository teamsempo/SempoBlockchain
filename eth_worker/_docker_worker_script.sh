#!/usr/bin/env bash
echo Container mode: $CONTAINER_MODE
echo Container type: $CONTAINER_TYPE

sleep 10

WORKER_CONCURRENCY=4

echo "Running docker worker script"

if [ "$CONTAINER_MODE" == 'ETH_WORKER_TEST' ]; then
    if [ "$CONTAINER_TYPE" == 'PRIMARY' ]; then
        echo "Running alembic upgrade (Default)"
        alembic upgrade head
        ret=$?
        if [ "$ret" -ne 0 ]; then
            exit $ret
        fi
        coverage run -m pytest test_eth_worker -x -v
        ret=$?
        if [ "$ret" -ne 0 ]; then
          exit $ret
        fi
        if [ ! -z "$CODECOV_TOKEN" ]; then # only report if CODECOV_TOKEN is set
          bash <(curl -s https://codecov.io/bash) -cF python
        fi
    else
        echo pass
        sleep infinity
    fi
else
    if [ "$CONTAINER_TYPE" == 'BEAT' ]; then
        echo "Starting Beat Worker"
        celery -A eth_manager beat --loglevel=WARNING
    elif [ "$CONTAINER_TYPE" == 'FLOWER' ]; then
        echo "Starting Flower Worker"
        flower -A worker --port=5555
    elif [ "$CONTAINER_TYPE" == 'PROCESSOR' ]; then
        echo "Starting Processor Worker"
        celery -A eth_manager worker --loglevel=INFO --concurrency=$WORKER_CONCURRENCY --pool=eventlet -Q=processor --without-gossip --without-mingle
    elif [ "$CONTAINER_TYPE" == 'LOW_PRIORITY_WORKER' ]; then
        echo "Starting Low Priority Worker"
        celery -A eth_manager worker --loglevel=INFO --concurrency=$WORKER_CONCURRENCY --pool=eventlet -Q=low-priority,celery --without-gossip --without-mingle
    elif [ "$CONTAINER_TYPE" == 'HIGH_PRIORITY_WORKER' ]; then
        echo "Starting High Priority Worker"
        celery -A eth_manager worker --loglevel=INFO --concurrency=$WORKER_CONCURRENCY --pool=eventlet -Q=high-priority --without-gossip --without-mingle
    elif [ "$CONTAINER_TYPE" == 'ANY_PRIORITY_WORKER' ]; then
        echo "Starting Any Priority Worker"
        celery -A eth_manager worker --loglevel=INFO --concurrency=$WORKER_CONCURRENCY --pool=eventlet -Q=low-priority,celery,high-priority,processor --without-gossip --without-mingle
    else
#       Default to primary worker configuration - running alembic upgrade twice is fine.
        echo "Running alembic upgrade (Default)"
        alembic upgrade head
        ret=$?
        if [ "$ret" -ne 0 ]; then
            exit $ret
        fi
        echo "Starting Generic Worker (Default)"
        celery -A eth_manager worker --loglevel=INFO --concurrency=10 --pool=eventlet -Q=low-priority,celery,high-priority --without-gossip --without-mingle
    fi
fi
