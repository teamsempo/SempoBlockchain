import os
import sys

from celery import Celery
from celery.schedules import crontab


sys.path.append('..')
import config

celery_app = Celery('tasks',
                    broker=config.REDIS_URL,
                    backend=config.REDIS_URL,
                    task_serializer='json')

celery_app.conf.beat_schedule = {
    'manage-scheduled-bonus-issuance': {
        'task': 'bonuses.bonus_tasks.auto_disburse_daily_bonus',
        'schedule': crontab(minute=50, hour=23)
    }
}

import ge_worker.bonuses.bonus_tasks

