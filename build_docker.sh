#!/usr/bin/env bash

GIT_HASH=$(git rev-parse HEAD)

cd ./app

npm run build

cd ../

docker build -t server . -f ./app/Dockerfile --build-arg GIT_HASH=$GIT_HASH
docker build -t proxy ./proxy
docker build -t low_priority_eth_worker . -f ./eth_worker/Dockerfile --build-arg CONTAINER_TYPE=LOW_PRIORITY_WORKER
docker build -t high_priority_eth_worker . -f ./eth_worker/Dockerfile --build-arg CONTAINER_TYPE=HIGH_PRIORITY_WORKER
docker build -t pgbouncer . -f ./pgbouncer/Dockerfile
