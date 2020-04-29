#!/usr/bin/env bash

bash build_docker.sh

# REPOSITORY_URI=290492953667.dkr.ecr.ap-southeast-2.amazonaws.com/blockchaindemo

GIT_HASH=$(git rev-parse HEAD)

cd ../

sed "s|REPOSITORY_URI|$REPOSITORY_URI|g; s|TAG_SUFFIX|$GIT_HASH|g" awsDockerrunTemplate.json > Dockerrun.aws.json

eval $(aws ecr get-login --no-include-email --region $ECR_REGION --profile $ECR_BUILDER);

docker tag server:latest $REPOSITORY_URI:server_$GIT_HASH
docker push $REPOSITORY_URI:server_$GIT_HASH

docker tag proxy:latest $REPOSITORY_URI:proxy_$GIT_HASH
docker push $REPOSITORY_URI:proxy_$GIT_HASH

docker tag eth_worker:latest $REPOSITORY_URI:eth_worker_$GIT_HASH
docker push $REPOSITORY_URI:eth_worker_$GIT_HASH

docker tag pgbouncer:latest $REPOSITORY_URI:pgbouncer_$GIT_HASH
docker push $REPOSITORY_URI:pgbouncer_$GIT_HASH
