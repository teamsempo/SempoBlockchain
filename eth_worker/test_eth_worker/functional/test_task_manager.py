import pytest
from utils import str_uuid, deterministic_address_1

from eth_src.sql_persistence.models import BlockchainTask

def test_duplicate_task_uuids_not_accepted(manager, dummy_wallet, db_session):
    uuid = str_uuid()

    t1 = manager.send_eth(uuid, 100, deterministic_address_1, dummy_wallet.address)

    t2 = manager.send_eth(uuid, 100, deterministic_address_1, dummy_wallet.address)

    matching_tasks = db_session.query(BlockchainTask).filter(BlockchainTask.uuid == uuid).all()

    assert len(matching_tasks) == 1
    assert t1 == t2
    assert matching_tasks[0].id == t1