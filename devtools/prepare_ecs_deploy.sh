#!/usr/bin/env bash

GIT_HASH=$(git rev-parse HEAD)

cd ../app

npm install

npm run build

cd ../
docker-compose -f docker-compose.ecs.yml build
GIT_HASH=$(git rev-parse HEAD)

cd ../

ECR_REGION="${ECR_REGION:-"ap-southeast-2"}"
APP_REPOSITORY_URI="${APP_REPOSITORY_URI:-"290492953667.dkr.ecr.ap-southeast-2.amazonaws.com/app"}"
WORKER_REPOSITORY_URI="${WORKER_REPOSITORY_URI:-"290492953667.dkr.ecr.ap-southeast-2.amazonaws.com/eth_worker"}"

eval $(aws ecr get-login --no-include-email --region $ECR_REGION);

docker tag server:latest $APP_REPOSITORY_URI:server_$GIT_HASH
docker push $APP_REPOSITORY_URI:server_$GIT_HASH

docker tag eth_worker:latest $WORKER_REPOSITORY_URI:eth_worker_$GIT_HASH
docker push $WORKER_REPOSITORY_URI:eth_worker_$GIT_HASH
