#!/usr/bin/env bash

celery beat -S redbeat.RedBeatScheduler -A eth_manager --loglevel=WARNING
