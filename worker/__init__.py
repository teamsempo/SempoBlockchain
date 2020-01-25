import sentry_sdk
from celery import Celery, beat
import redis

import config

sentry_sdk.init(config.SENTRY_SERVER_DSN, release=config.VERSION)

celery_app = Celery('tasks',
                    broker=config.REDIS_URL,
                    backend=config.REDIS_URL,
                    task_serializer='json')

red = redis.Redis.from_url(config.REDIS_URL)

if config.IS_USING_BITCOIN:
    celery_app.conf.beat_schedule = {
        "test_task": {
            "task": "worker.celery_tasks.find_new_ouputs",
            "schedule": 24.0
        },
    }
else:
    celery_app.conf.beat_schedule = {
        "test_task": {
            "task": "worker.celery_tasks.find_new_external_inbounds",
            "schedule": 10.0
        },
    }

import worker.celery_tasks
