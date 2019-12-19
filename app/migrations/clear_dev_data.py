import subprocess
from sqlalchemy import create_engine
import sys
import os

dirname = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(dirname, "..", "..")))
sys.path.append(os.path.abspath(os.path.join(dirname, "..")))

import config
from server.models.utils import ModelBase as ServerModelBase
from eth_worker.sql_persistence.models import ModelBase as EthModelBase


def drop_and_rebuild_sql(base, uri):
    engine = create_engine(uri)
    print(f'Dropping for uri: {uri}')
    base.metadata.drop_all(engine)
    print(f'Creating for uri: {uri}')
    base.metadata.create_all(engine)


def clear_all():
    drop_and_rebuild_sql(ServerModelBase, config.SQLALCHEMY_DATABASE_URI)
    drop_and_rebuild_sql(EthModelBase, config.ETH_DATABASE_URI)


    print('Resetting Ganache')

    subprocess.Popen(["rm", "-R", "./ganacheDB"])
    subprocess.Popen(["mkdir", "./ganacheDB"])


if __name__ == '__main__':
clear_all()