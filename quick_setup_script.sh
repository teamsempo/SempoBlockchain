#!/usr/bin/env bash
set -m

PYTHONUNBUFFERED=1

source $1

if [ -z ${MASTER_WALLET_PK+x} ]
then
echo "\$MASTER_WALLET_PK is empty"
exit 0
fi

echo "This will wipe ALL local Sempo data."
echo "Persist Ganache? y/N"
read ganachePersistInput

echo "Create Dev Data? (s)mall/(m)edium/(l)arge/(N)o"
read testDataInput

if [ "$testDataInput" == 's' ]; then
    echo "Creating Small Dev Dataset"
    testdata='small'
elif [ "$testDataInput" == 'm' ]; then
    echo "Creating Medium Dev Dataset"
    testdata='medium'
elif [ "$testDataInput" == 'l' ]; then
    echo "Creating Large Dev Dataset"
    testdata='large'
else
    echo "Not Creating Dev Dataset"
    testdata='none'
fi

set +e

echo ~~~~Killing any leftover workers or app
kill -9 $(ps aux | grep '[r]un.py' | awk '{print $2}')
kill -9 $(ps aux | grep '[c]elery' | awk '{print $2}')

echo ~~~~Resetting readis
redis-server &
redis-cli FLUSHALL

sleep 1

echo ~~~~Resetting postgres
echo If this section hangs, you might have a bunch of idle postgres connections. Kill them using
echo "sudo kill -9 \$(ps aux | grep '[p]ostgres .* idle' | awk '{print \$2}')"

db_server=postgres://${DB_USER:-postgres}:${DB_PASSWORD:-password}@localhost:5432
app_db=$db_server/${APP_DB:-sempo_app}
eth_worker_db=$db_server/${WORKER_DB:-eth_worker}

set -e
psql $db_server -c ''

set +e

psql $db_server -c "DROP DATABASE IF EXISTS ${APP_DB:-sempo_app}"
psql $db_server -c "DROP DATABASE IF EXISTS ${WORKER_DB:-sempo_eth_worker}"
psql $db_server -c "CREATE DATABASE ${APP_DB:-sempo_app}"
psql $db_server -c "CREATE DATABASE ${WORKER_DB:-sempo_eth_worker}"

cd app
python manage.py db upgrade

cd ../eth_worker/
alembic upgrade heads

echo ~~~~Resetting Ganache
cd ../
kill $(ps aux | grep '[g]anache-cli' | awk '{print $2}')

if [ $ganachePersistInput != y ]
then
  ganache-cli -l 80000000 -i 42 --account="${MASTER_WALLET_PK},10000000000000000000000000" &
else
  rm -R ./ganacheDB
  mkdir ganacheDB
  ganache-cli -l 80000000 -i 42 --account="${MASTER_WALLET_PK},10000000000000000000000000" --db './ganacheDB' &
fi

sleep 5

set -e

echo ~~~Starting worker
cd eth_worker
celery -A eth_manager worker --loglevel=INFO --concurrency=8 --pool=eventlet -Q processor,celery &
sleep 5

echo ~~~Seeding Data
cd ../app/migrations/
python -u seed.py

echo ~~~Starting App

cd ../
python -u run.py &
sleep 10

echo ~~~Creating Default Account
curl 'http://0.0.0.0:9000/api/v1/auth/register/'  -H 'Content-Type: application/json' -H 'Origin: http://0.0.0.0:9000' --data-binary '{"username":"admin@acme.org","password":"C0rrectH0rse","referral_code":null}' --compressed --insecure
psql $app_db -c 'UPDATE public."user" SET is_activated=TRUE'

echo ~~~Setting up Contracts
cd ../
python -u contract_setup_script.py

if [ "$testdata" != 'none' ]; then
    echo ~~~Creating test data
    cd ./app/migrations/
    python -u dev_data.py ${testdata}
fi

echo ~~~Killing Python Processes
sleep 5
set +e
kill -9 $(ps aux | grep '[r]un.py' | awk '{print $2}')
kill -9 $(ps aux | grep '[c]elery' | awk '{print $2}')
sleep 2

echo ~~~Done Setup! Bringing Ganache to foreground
fg 2

