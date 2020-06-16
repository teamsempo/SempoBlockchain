#!/usr/bin/env bash

#echo cheese

celery beat -S redbeat.RedBeatScheduler -A eth_manager --loglevel=WARNING
#-A worker worker --loglevel=INFO --concurrency=500 --pool=eventlet
