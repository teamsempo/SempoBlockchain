#!/usr/bin/env bash

#echo cheese

celery -A worker beat --loglevel=WARNING

#-A worker worker --loglevel=INFO --concurrency=500 --pool=gevent