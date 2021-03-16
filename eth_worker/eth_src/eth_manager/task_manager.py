from typing import Optional
from celery import signature

import celery_utils
from celery_utils import eth_endpoint
from sempo_types import UUID, UUIDList

from eth_manager.transaction_supervisor import TransactionSupervisor
from eth_manager.eth_transaction_processor import EthTransactionProcessor

class TaskManager(object):
    """
    A factory for creating tasks, which represent an action that must be completed on the blockchain.
    These are then picked up by the TransactionSupervisor which will in turn instruct
    the EthTransactionProcessor on making transaction attempts.
    """

    def transact_with_contract_function(
            self,
            uuid: UUID,
            contract_address: str, abi_type: str, function_name: str,
            args: Optional[tuple] = None, kwargs: Optional[dict] = None,
            signing_address: Optional[str] = None, encrypted_private_key: Optional[str] = None,
            gas_limit: Optional[int] = None,
            prior_tasks: Optional[UUIDList] = None,
            posterior_tasks: Optional[UUIDList] = None,
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
        :param posterior_tasks: a uuid list of tasks for which this task must succeed before they will be attempted
        :param reserves_task: DEPRECATED - reverses an old task
        :return: task_id
        """

        create_kwargs = {
            'uuid': uuid,
            'contract_address': contract_address,
            'abi_type': abi_type,
            'function_name': function_name,
            'args': args,
            'kwargs': kwargs,
            'gas_limit': gas_limit,
            'prior_tasks': prior_tasks,
            'posterior_tasks': posterior_tasks,
        }

        return self._create_task(
            signing_address,
            encrypted_private_key,
            self.persistence.create_function_task,
            create_kwargs
        )

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

        create_kwargs = {
            'uuid': uuid,
            'recipient_address': recipient_address,
            'amount_wei': amount_wei,
            'prior_tasks': prior_tasks,
            'posterior_tasks': posterior_tasks,
        }

        return self._create_task(
            signing_address,
            encrypted_private_key,
            self.persistence.create_send_eth_task,
            create_kwargs
        )

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

        create_kwargs = {
            'uuid': uuid,
            'contract_name': contract_name,
            'args': args,
            'kwargs': kwargs,
            'gas_limit': gas_limit,
            'prior_tasks': prior_tasks
        }

        return self._create_task(
            signing_address,
            encrypted_private_key,
            self.persistence.create_deploy_contract_task,
            create_kwargs
        )

    def _create_task(self, signing_address, encrypted_private_key, create_method, create_kwargs):

        uuid = create_kwargs['uuid']

        existing_task = self.persistence.get_task_from_uuid(uuid)

        if existing_task:
            return existing_task.id

        signing_wallet_obj = self.persistence.get_signing_wallet_object(
            signing_address,
            encrypted_private_key
        )

        create_kwargs['signing_wallet_obj'] = signing_wallet_obj

        task = create_method(**create_kwargs)

        self._queue_attempt_transaction(task.uuid)

        return task.id

    def remove_prior_task_dependency(self, task_uuid: UUID, prior_task_uuid: UUID):
        """
        For a task specified by task_uuid, removes its dependency on a prior task specified by prior_task_uuid.
        This is useful for when a prior task cannot be completed for some reason and even though we're confident that
        skipping it would be fine, it blocks all downstream dependent tasks.
        Includes an attempt_transaction, so that if the task can now be completed because it's unblocked, it will do so.
        WARNING: Using this is dangerous as it overrides the expected transaction order. Do so at your own risk!!
        If a task is stuck for whatever reason, it is generally better to unstick the task (perhaps by topping up an
        account balance) and then use retry_task, than it is to call this.
        :param task_uuid: the task that is blocked
        :param posterior_task_uuid: the blocking task
        :return:
        """

        self.persistence.remove_prior_task_dependency(task_uuid, prior_task_uuid)

        self._queue_attempt_transaction(task_uuid)

    def remove_all_posterior_dependencies(self, prior_task_uuid: UUID):
        """
        Bulk version of 'remove_prior_task_dependency' that removes all the dependencies on a task specified by
        prior_task_uuid.
        Like 'remove_prior_task_dependency', attempts any potentially unblocked tasks.
        WARNING: The same dangers that apply to 'remove_prior_task_dependency' also apply here, but moreso.
        :param prior_task_uuid: the blocking task
        """

        posterior_task_uuids = self.persistence.remove_all_posterior_dependencies(prior_task_uuid)

        for uuid in posterior_task_uuids:
            self._queue_attempt_transaction(uuid)

    def retry_task(self, task_uuid: UUID):
        task = self.persistence.get_task_from_uuid(task_uuid)
        needs_retry = True

        if task:
            for transaction in task.transactions:
                result = self.processor.get_transaction_status(transaction.id)

                status = result.get('status')

                if status == 'SUCCESS':

                    print(f'Task with id {task.id} has already completed! Skipping')
                    self.persistence.update_transaction_data(transaction.id, result)
                    self.persistence.set_task_status_text(task, 'SUCCESS')

                    unstarted_posteriors = self.persistence.get_unstarted_posteriors(task.uuid)

                    for dep_task in unstarted_posteriors:
                        print('Starting posterior task: {}'.format(dep_task.uuid))
                        self._queue_attempt_transaction(dep_task.uuid)

                    needs_retry = False

                    break

        if needs_retry:
            self.persistence.increment_task_invocations(task_uuid)
            self._queue_attempt_transaction(task_uuid)

    def retry_failed(self, min_task_id, max_task_id, retry_unstarted=False):

        print(f'Testings Task from {min_task_id} to {max_task_id}, retrying unstarted={retry_unstarted}')
        needing_retry = self.persistence.get_failed_tasks(min_task_id, max_task_id)
        pending_tasks = self.persistence.get_pending_tasks(min_task_id, max_task_id)

        print(f"{len(needing_retry)} tasks currently with failed state")
        print(f"{len(pending_tasks)} tasks currently pending")

        unstarted_tasks = None
        if retry_unstarted:
            unstarted_tasks = self.persistence.get_unstarted_tasks(min_task_id, max_task_id)
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

    def _queue_attempt_transaction(self, task_uuid):
        celery_utils.queue_sig(
            self.transaction_supervisor.sigs.attempt_transaction(task_uuid)
        )

    def __init__(self, persistence, transaction_supervisor: TransactionSupervisor):

        self.persistence = persistence

        self.transaction_supervisor = transaction_supervisor

        self.sigs = SigGenerators()

        self.processor = transaction_supervisor.processor


class SigGenerators(object):

    def deploy_contract_task(
            self,
            signing_address,
            contract_name,
            args=None,
            prior_tasks=None
    ):

        return signature(
            eth_endpoint('deploy_contract'),
            kwargs={
                'signing_address': signing_address,
                'contract_name': contract_name,
                'args': args,
                'prior_tasks': prior_tasks
            })

    def transact_with_function_task(
            self,
            signing_address,
            contract_address,
            contract_type,
            func,
            args=None,
            gas_limit=None,
            prior_tasks=None,
            reverses_task=None
    ):

        kwargs = {
            'signing_address': signing_address,
            'contract_address': contract_address,
            'abi_type': contract_type,
            'function': func,
            'args': args,
            'prior_tasks': prior_tasks,
            'reverses_task': reverses_task
        }

        if gas_limit:
            kwargs['gas_limit'] = gas_limit

        return signature(eth_endpoint('transact_with_contract_function'), kwargs=kwargs)

    def send_eth_task(
            self,
            signing_address,
            amount_wei,
            recipient_address
    ):
        return signature(
            eth_endpoint('send_eth'),
            kwargs={
                'signing_address': signing_address,
                'amount_wei': amount_wei,
                'recipient_address': recipient_address
            }
        )