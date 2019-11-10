import pytest
import os
import sys
import subprocess
from sql_persistence import models as eth_models
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from celery import Celery
from celery.bin import worker

import config

os.environ['DEPLOYMENT_NAME'] = "TEST"


p1 = subprocess.Popen(["alembic", "upgrade", "heads"], cwd="./eth_worker")

p1.wait()

# raise Exception("This script should only be used against test configs (it will wipe your eth_worker db)")
# engine = create_engine(config.ETH_DATABASE_URI)
# eth_models.ModelBase.metadata.drop_all(engine)
# eth_models.ModelBase.metadata.create_all(engine)

p2 = subprocess.Popen(["celery", "-A", "eth_manager", "worker",
                       "--loglevel=INFO", "--concurrency=4", "--pool=eventlet"], cwd="./eth_worker")


p3 = subprocess.Popen(["celery", "-A", "eth_manager", "worker",
                       "--loglevel=INFO", "--concurrency=1", "--pool=eventlet", "-Q=processor"], cwd="./eth_worker")


p2.wait()




