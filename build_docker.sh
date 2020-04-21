#!/usr/bin/env bash

GIT_HASH=$(git rev-parse HEAD)

cd ./app

npm run build

cd ../

docker build -t server . -f ./app/Dockerfile --build-arg GIT_HASH=$GIT_HASH
docker build -t proxy ./proxy
docker build -t eth_worker . -f ./eth_worker/Dockerfile
docker build -t pgbouncer . -f ./pgbouncer/Dockerfile