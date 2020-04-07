#!/usr/bin/env bash
set -m

PYTHONUNBUFFERED=1

source $1

echo "This will wipe ALL local Sempo data."
echo "Persist Ganache? (y/N)"
read ganachePersistInput

if [ -z ${MASTER_WALLET_PK+x} ]
then
echo "\$MASTER_WALLET_PK is empty"
exit 0
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
app_db=$db_server/${APP_DB:-sempo_blockchain_local}
eth_worker_db=$db_server/${APP_DB:-eth_worker}

psql $app_db -c 'DROP SCHEMA public CASCADE'
psql $app_db -c 'CREATE SCHEMA public'

psql $eth_worker_db -c 'DROP SCHEMA public CASCADE'
psql $eth_worker_db -c 'CREATE SCHEMA public'


cd app
python manage.py db upgrade

cd ../eth_worker/
alembic upgrade heads

echo ~~~~Resetting Ganache
cd ../
kill $(ps aux | grep '[g]anache-cli' | awk '{print $2}')
rm -R ./ganacheDB

if [ $ganachePersistInput != y ]
then
  ganache-cli -l 80000000 -i 42 --account="${MASTER_WALLET_PK},10000000000000000000000000" &
else
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
sleep 5

echo ~~~Creating Default Account
curl 'http://0.0.0.0:9000/api/v1/auth/register/' -H 'Connection: keep-alive' -H 'Accept: application/json' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36' -H 'Content-Type: application/json' -H 'Origin: http://0.0.0.0:9000' -H 'Referer: http://0.0.0.0:9000/login/sign-up' -H 'Accept-Language: en-US,en;q=0.9' -H 'Cookie: _ga=GA1.1.889304486.1568334223; _hp2_id.2461187681=%7B%22userId%22%3A%221109895996535790%22%2C%22pageviewId%22%3A%224425033411764656%22%2C%22sessionId%22%3A%221479247222978424%22%2C%22identity%22%3Anull%2C%22trackerVersion%22%3A%224.0%22%7D' --data-binary '{"username":"admin@acme.org","password":"C0rrectH0rse","referral_code":null}' --compressed --insecure
psql $app_db -c 'UPDATE public."user" SET is_activated=TRUE'

echo ~~~Setting up Contracts
cd ../
python -u contract_setup_script.py

echo ~~~Killing Python Processes
sleep 5
set +e
kill -9 $(ps aux | grep '[r]un.py' | awk '{print $2}')
kill -9 $(ps aux | grep '[c]elery' | awk '{print $2}')

echo ~~~Done Setup! Bringing Ganache to foreground
fg 2

