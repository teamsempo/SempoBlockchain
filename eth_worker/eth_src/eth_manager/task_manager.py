from typing import Optional

from celery_dispatchers.regular import queue_attempt_transaction
from sempo_types import UUID, UUIDList


class TaskManager(object):

    def transact_with_contract_function(
            self,
            uuid: UUID,
            contract_address: str, abi_type: str, function_name: str,
            args: Optional[tuple] = None, kwargs: Optional[dict] = None,
            signing_address: Optional[str] = None, encrypted_private_key: Optional[str] = None,
            gas_limit: Optional[int] = None,
            prior_tasks: Optional[UUIDList] = None,
            reserves_task: Optional[UUID] = None
    ):
        """
        The main transaction entrypoint for the processor.
        :param uuid: the celery generated uuid for the task
        :param contract_address: the address of the contract for the function
        :param abi_type: the type of ABI for the contract being called
        :param function_name: name of the function
        :param args: arguments for the function
        :param kwargs: keyword arguments for the function
        :param signing_address: address of the wallet signing the txn
        :param encrypted_private_key: private key of the wallet making the transaction, encrypted using key from settings
        :param gas_limit: limit on the amount of gas txn can use. Overrides system default
        :param prior_tasks: a list of task uuids that must succeed before this task will be attempted,
        :param reserves_task: the uuid of a task that this task reverses. can only be a transferFrom
        :return: task_id
        """

        signing_wallet_obj = self.persistence_interface.get_signing_wallet_object(
            signing_address,
            encrypted_private_key
        )

        task = self.persistence_interface.create_function_task(uuid,
                                                               signing_wallet_obj,
                                                               contract_address, abi_type,
                                                               function_name, args, kwargs,
                                                               gas_limit, prior_tasks, reserves_task)

        # Attempt Create Async Transaction
        queue_attempt_transaction(task.uuid)

    def send_eth(self,
                 uuid: UUID,
                 amount_wei: int,
                 recipient_address: str,
                 signing_address: Optional[str] = None, encrypted_private_key: Optional[str] = None,
                 prior_tasks: Optional[UUIDList] = None,
                 posterior_tasks: Optional[UUIDList] = None):
        """
        The main entrypoint sending eth.

        :param uuid: the celery generated uuid for the task
        :param amount_wei: the amount in WEI to send
        :param recipient_address: the recipient address
        :param signing_address: address of the wallet signing the txn
        :param encrypted_private_key: private key of the wallet making the transaction, encrypted using key from settings
        :param prior_tasks: a list of task uuids that must succeed before this task will be attempted
        :param posterior_tasks: a uuid list of tasks for which this task must succeed before they will be attempted
        :return: task_id
        """

        signing_wallet_obj = self.persistence_interface.get_signing_wallet_object(
            signing_address,
            encrypted_private_key
        )

        task = self.persistence_interface.create_send_eth_task(uuid,
                                                               signing_wallet_obj,
                                                               recipient_address, amount_wei,
                                                               prior_tasks,
                                                               posterior_tasks)

        # Attempt Create Async Transaction
        queue_attempt_transaction(task.uuid)

    def deploy_contract(
            self,
            uuid: UUID,
            contract_name: str,
            args: Optional[tuple] = None, kwargs: Optional[dict] = None,
            signing_address: Optional[str] = None, encrypted_private_key: Optional[str] = None,
            gas_limit: Optional[int] = None,
            prior_tasks: Optional[UUIDList] = None
    ):
        """
        The main deploy contract entrypoint for the processor.

        :param uuid: the celery generated uuid for the task
        :param contract_name: System will attempt to fetched abi and bytecode from this
        :param args: arguments for the constructor
        :param kwargs: keyword arguments for the constructor
        :param signing_address: address of the wallet signing the txn
        :param encrypted_private_key: private key of the wallet making the transaction, encrypted using key from settings
        :param gas_limit: limit on the amount of gas txn can use. Overrides system default
        :param prior_tasks: a list of task uuid that must succeed before this task will be attempted
        """

        signing_wallet_obj = self.persistence_interface.get_signing_wallet_object(
            signing_address,
            encrypted_private_key
        )

        task = self.persistence_interface.create_deploy_contract_task(uuid,
                                                                      signing_wallet_obj,
                                                                      contract_name,
                                                                      args, kwargs,
                                                                      gas_limit,
                                                                      prior_tasks)

        # Attempt Create Async Transaction
        queue_attempt_transaction(task.uuid)

    def retry_task(self, task_uuid: UUID):
        self.persistence_interface.increment_task_invocations(task_uuid)
        queue_attempt_transaction(task_uuid)

    def retry_failed(self, min_task_id, max_task_id, retry_unstarted=False):

        print(f'Testings Task from {min_task_id} to {max_task_id}, retrying unstarted={retry_unstarted}')

        needing_retry = self.persistence_interface.get_failed_tasks(min_task_id, max_task_id)
        pending_tasks = self.persistence_interface.get_pending_tasks(min_task_id, max_task_id)

        print(f"{len(needing_retry)} tasks currently with failed state")
        print(f"{len(pending_tasks)} tasks currently pending")

        unstarted_tasks = None
        if retry_unstarted:
            unstarted_tasks = self.persistence_interface.get_unstarted_tasks(min_task_id, max_task_id)
            print(f"{len(unstarted_tasks)} tasks currently unstarted")

            needing_retry = needing_retry + unstarted_tasks

            needing_retry.sort(key=lambda t: t.id)

        for task in needing_retry:
            self.retry_task(task.uuid)

        return {
            'failed_count': len(needing_retry),
            'pending_count': len(pending_tasks),
            'unstarted_count': len(unstarted_tasks) if unstarted_tasks else 'Unknown'
        }

    def __init__(self, persistence_module):

            self.persistence_interface = persistence_module

