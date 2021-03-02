#!/usr/bin/env bash

GIT_HASH=$(git rev-parse HEAD)

cd ../app

npm install

npm run build

cd ../

docker-compose build