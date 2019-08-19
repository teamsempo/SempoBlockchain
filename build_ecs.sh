#!/usr/bin/env bash

GIT_HASH=$(git rev-parse HEAD)


REPOSITORY_URI=290492953667.dkr.ecr.ap-southeast-2.amazonaws.com/blockchaindemo

cd ./app

npm run build

cd ../

docker build -t server . -f ./app/Dockerfile --build-arg GIT_HASH=$GIT_HASH
docker build -t proxy ./proxy
docker build -t worker . -f ./worker/Dockerfile

eval $(aws ecr get-login --no-include-email --region ap-southeast-2 --profile ECS);

docker tag server:latest $REPOSITORY_URI:server
docker push $REPOSITORY_URI:server

docker tag proxy:latest $REPOSITORY_URI:proxy
docker push $REPOSITORY_URI:proxy

docker tag worker:latest $REPOSITORY_URI:worker
docker push $REPOSITORY_URI:worker
