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


def test_removal_of_priors(manager, dummy_wallet, db_session, mock_queue_sig):

    uuid1 = str_uuid()
    uuid2 = str_uuid()
    uuid3 = str_uuid()

    manager.send_eth(uuid1, 100, deterministic_address_1, dummy_wallet.address)
    db_session.commit()

    # Create two tasks, both dependent on task 1
    manager.send_eth(uuid2, 100, deterministic_address_1, dummy_wallet.address, prior_tasks=[uuid1])
    db_session.commit()

    manager.send_eth(uuid3, 100, deterministic_address_1, dummy_wallet.address, prior_tasks=[uuid1])
    db_session.commit()

    task_1 = db_session.query(BlockchainTask).filter(BlockchainTask.uuid == uuid1).first()
    task_2 = db_session.query(BlockchainTask).filter(BlockchainTask.uuid == uuid2).first()
    task_3 = db_session.query(BlockchainTask).filter(BlockchainTask.uuid == uuid3).first()

    assert task_1.posterior_tasks == [task_2, task_3]
    assert task_2.prior_tasks == [task_1]

    manager.remove_prior_task_dependency(uuid2, uuid1)

    # Make sure only the task1<>task2 dependency is removed
    assert task_1.posterior_tasks == [task_3]
    assert task_2.prior_tasks == []
    assert task_3.prior_tasks == [task_1]

    sig_output = mock_queue_sig[-1][0]

    # Make sure task2 is sent to the queue for retry
    assert sig_output.task == 'celery_tasks.attempt_transaction'
    assert sig_output.kwargs == {'task_uuid': uuid2}


def test_remove_all_posterior_dependencies(manager, dummy_wallet, db_session, mock_queue_sig):

    uuid0 = str_uuid()
    uuid1 = str_uuid()
    uuid2 = str_uuid()
    uuid3 = str_uuid()

    # Include a task 0 that we won't remove dependencies for
    manager.send_eth(uuid0, 100, deterministic_address_1, dummy_wallet.address)
    db_session.commit()

    manager.send_eth(uuid1, 100, deterministic_address_1, dummy_wallet.address)
    db_session.commit()

    # Create two tasks, both dependent on task 1 and task 0
    manager.send_eth(uuid2, 100, deterministic_address_1, dummy_wallet.address, prior_tasks=[uuid1, uuid0])
    db_session.commit()

    manager.send_eth(uuid3, 100, deterministic_address_1, dummy_wallet.address, prior_tasks=[uuid1, uuid0])
    db_session.commit()

    task_0 = db_session.query(BlockchainTask).filter(BlockchainTask.uuid == uuid0).first()
    task_1 = db_session.query(BlockchainTask).filter(BlockchainTask.uuid == uuid1).first()
    task_2 = db_session.query(BlockchainTask).filter(BlockchainTask.uuid == uuid2).first()
    task_3 = db_session.query(BlockchainTask).filter(BlockchainTask.uuid == uuid3).first()

    assert task_0.posterior_tasks == [task_2, task_3]
    assert task_1.posterior_tasks == [task_2, task_3]
    assert task_2.prior_tasks == [task_0, task_1]
    assert task_3.prior_tasks == [task_0, task_1]

    manager.remove_all_posterior_dependencies(uuid1)

    # Make sure all posterior dependencies are removed, but other priors are unaffected
    assert task_1.posterior_tasks == []
    assert task_2.prior_tasks == [task_0]
    assert task_3.prior_tasks == [task_0]

    sig_output1 = mock_queue_sig[-2][0]
    sig_output2 = mock_queue_sig[-1][0]

    # Make sure task2 is sent to the queue for retry
    assert sig_output1.task == 'celery_tasks.attempt_transaction'
    assert sig_output1.kwargs == {'task_uuid': uuid2}

    # Make sure task3 is sent to the queue for retry
    assert sig_output2.task == 'celery_tasks.attempt_transaction'
    assert sig_output2.kwargs == {'task_uuid': uuid3}