#!/usr/bin/env bash

bash build_docker.sh

eval $(aws ecr get-login --no-include-email --region $ECR_REGION --profile ECR_BUILDER);

docker tag server:latest $REPOSITORY_URI:server
docker push $REPOSITORY_URI:server

docker tag proxy:latest $REPOSITORY_URI:proxy
docker push $REPOSITORY_URI:proxy

docker tag eth_worker:latest $REPOSITORY_URI:eth_worker
docker push $REPOSITORY_URI:eth_worker
