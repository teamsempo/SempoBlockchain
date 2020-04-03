#!/usr/bin/env bash

bash build_docker.sh
REPOSITORY_URI=290492953667.dkr.ecr.ap-southeast-2.amazonaws.com/blockchaindemo
TAG_SUFFIX=test

sed "s|REPOSITORY_URI|$REPOSITORY_URI|g; s|TAG_SUFFIX||g" awsDockerrunTemplate.json > Dockerrun.aws.json

eval $(aws ecr get-login --no-include-email);

docker tag server:latest $REPOSITORY_URI:server
docker push $REPOSITORY_URI:server

docker tag proxy:latest $REPOSITORY_URI:proxy
docker push $REPOSITORY_URI:proxy

docker tag pgbouncer:latest $REPOSITORY_URI:pgbouncer
docker push $REPOSITORY_URI:pgbouncer

docker tag eth_worker:latest $REPOSITORY_URI:eth_worker
docker push $REPOSITORY_URI:eth_worker
