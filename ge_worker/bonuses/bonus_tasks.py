import os
import sys

parent_directory = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))
sys.path.append(parent_directory)
sys.path.append(os.getcwd())


from ge_worker.bonuses import celery_app
from ge_worker.bonuses.bonus_processor import BonusProcessor


@celery_app.task()
def auto_disburse_daily_bonus():
    bonus_processor = BonusProcessor(issuable_amount=1000)
    return bonus_processor.auto_disburse_daily_bonus()
