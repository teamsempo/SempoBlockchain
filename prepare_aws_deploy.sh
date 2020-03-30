#!/usr/bin/env bash

#bash build_docker.sh

sed "s|REPOSITORY_URI|$REPOSITORY_URI|g; s|TAG_SUFFIX||g" awsDockerrunTemplate.json > Dockerrun.aws.json

eval $(aws ecr get-login --no-include-email --region $ECR_REGION --profile ECR_BUILDER);

docker tag server:latest $REPOSITORY_URI:server
docker push $REPOSITORY_URI:server

docker tag proxy:latest $REPOSITORY_URI:proxy
docker push $REPOSITORY_URI:proxy

docker tag pgbouncer:latest $REPOSITORY_URI:pgbouncer
docker push $REPOSITORY_URI:pgbouncer

docker tag low_priority_eth_worker:latest $REPOSITORY_URI:low_priority_eth_worker
docker push $REPOSITORY_URI:low_priority_eth_worker

docker tag high_priority_eth_worker:latest $REPOSITORY_URI:high_priority_eth_worker
docker push $REPOSITORY_URI:high_priority_eth_worker
