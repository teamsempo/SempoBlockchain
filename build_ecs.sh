#!/usr/bin/env bash

bash build_docker.sh

REPOSITORY_URI=290492953667.dkr.ecr.ap-southeast-2.amazonaws.com/blockchaindemo

eval $(aws ecr get-login --no-include-email --region ap-southeast-2 --profile ECS);

docker tag server:latest $REPOSITORY_URI:server
docker push $REPOSITORY_URI:server

docker tag proxy:latest $REPOSITORY_URI:proxy
docker push $REPOSITORY_URI:proxy

docker tag pgbouncer:latest $REPOSITORY_URI:pgbouncer
docker push $REPOSITORY_URI:pgbouncer

docker tag eth_worker:latest $REPOSITORY_URI:eth_worker
docker push $REPOSITORY_URI:eth_worker
