#!/usr/bin/env bash

bash build_docker.sh

GIT_HASH=$(git rev-parse HEAD)

cd ../

sed "s|REPOSITORY_URI|$REPOSITORY_URI|g; s|TAG_SUFFIX|$GIT_HASH|g" ./awsDockerrunTemplate.json > Dockerrun.aws.json

eval $(aws ecr get-login --no-include-email --region $ECR_REGION --profile $ECR_BUILDER);

docker tag server:latest $REPOSITORY_URI:server_$GIT_HASH
docker push $REPOSITORY_URI:server_$GIT_HASH

docker tag proxy:latest $REPOSITORY_URI:proxy_$GIT_HASH
docker push $REPOSITORY_URI:proxy_$GIT_HASH

docker tag eth_worker:latest $REPOSITORY_URI:eth_worker_$GIT_HASH
docker push $REPOSITORY_URI:eth_worker_$GIT_HASH

docker tag pgbouncer:latest $REPOSITORY_URI:pgbouncer_$GIT_HASH
docker push $REPOSITORY_URI:pgbouncer_$GIT_HASH

docker tag eth_worker:latest gcr.io/vocal-tracer-302110/eth_worker:a9803
docker push gcr.io/${PROJECT_ID}/eth_worker:a9803

docker tag server:latest gcr.io/vocal-tracer-302110/server:a9803
docker push gcr.io/vocal-tracer-302110/server:a9803

docker build -t gcr.io/vocal-tracer-302110/nginx:latest .
docker push gcr.io/vocal-tracer-302110/nginx:latest
