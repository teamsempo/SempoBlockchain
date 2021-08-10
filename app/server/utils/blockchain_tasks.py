from flask import g
import config
from typing import Optional, List, Dict
from functools import partial
from flask import current_app
from eth_keys import keys
from eth_utils import keccak
import os
import random
from time import sleep

from . import task_runner

from server.utils.exchange import (
    bonding_curve_tokens_to_reserve,
    bonding_curve_reserve_to_tokens,
    bonding_curve_token1_to_token2
)
from server.utils.multi_chain import get_chain

class BlockchainTasker(object):
    
    def _eth_endpoint(self, endpoint):
        celery_tasks_name = 'celery_tasks'
        return f'{get_chain()}.{celery_tasks_name}.{endpoint}'

    def _execute_synchronous_celery(self, task, kwargs=None, args=None, timeout=None, queue='high-priority'):
        async_result = task_runner.delay_task(task, kwargs, args, queue=queue)
        try:
            response = async_result.get(
                timeout=timeout or current_app.config['CHAINS'][get_chain()]['SYNCRONOUS_TASK_TIMEOUT'],
                propagate=True,
                interval=0.3)
        except Exception as e:
            raise e
        finally:
            async_result.forget()
        return response

    def _synchronous_call(self, contract_address, contract_type, func, args=None, signing_address=None, queue='high-priority'):
        kwargs = {
            'contract_address': contract_address,
            'abi_type': contract_type,
            'function': func,
            'args': args,
            'signing_address': signing_address
        }
        return self._execute_synchronous_celery(self._eth_endpoint('call_contract_function'), kwargs, queue=queue)

    def _transaction_task(self,
                          signing_address,
                          contract_address, contract_type,
                          func, args=None,
                          gas_limit=None,
                          prior_tasks=None,
                          queue=None,
                          task_uuid=None
                          ):
        kwargs = {
            'signing_address': signing_address,
            'contract_address': contract_address,
            'abi_type': contract_type,
            'function': func,
            'args': args,
            'gas_limit': gas_limit,
            'prior_tasks': prior_tasks
        }
        return task_runner.delay_task(
            self._eth_endpoint('transact_with_contract_function'),
            kwargs=kwargs, queue=queue, task_uuid=task_uuid
        ).id

    def add_transaction_sync_filter(self, kwargs):
        task_runner.delay_task(self._eth_endpoint('add_transaction_filter'), kwargs = kwargs)
        return True

    def force_third_party_transaction_sync(self):
        return task_runner.delay_task(self._eth_endpoint('synchronize_third_party_transactions'), queue='low-priority').id

    def force_fetch_block_range(self, filter_address, floor, ceiling):
        return self._execute_synchronous_celery(self._eth_endpoint('force_fetch_block_range'), { 'filter_address': filter_address, 'floor': floor, 'ceiling': ceiling })

    def force_recall_webhook(self, transaction_hash):
        return self._execute_synchronous_celery(self._eth_endpoint('force_recall_webhook'), { 'transaction_hash': transaction_hash })

    def get_third_party_sync_metrics(self):
        return self._execute_synchronous_celery(self._eth_endpoint('get_third_party_sync_metrics'), {})

    def get_failed_callbacks(self):
        return self._execute_synchronous_celery(self._eth_endpoint('get_failed_callbacks'), {})

    def get_blockchain_task(self, task_uuid):
        """
        Used to check the status of a blockchain task

        :param task_uuid: uuid of the blockchain
        :return: Serialised Task Dictionary:
        {
            status: enum, one of 'SUCCESS', 'PENDING', 'UNSTARTED', 'FAILED', 'UNKNOWN'
            priors: list of prior task uuids
        }
        """
        return self._execute_synchronous_celery(self._eth_endpoint('get_task'), {'task_uuid': task_uuid})

    def await_task_success(self,
                           task_uuid,
                           timeout=None,
                           poll_frequency=0.5):
        elapsed = 0

        if timeout is None:
            timeout = current_app.config['CHAINS'][get_chain()]['SYNCRONOUS_TASK_TIMEOUT']

        while timeout is None or elapsed <= timeout:
            task = self.get_blockchain_task(task_uuid)
            if task is None:
                return None

            if task['status'] == 'SUCCESS':
                return task
            else:
                sleep(poll_frequency)
                elapsed += poll_frequency

        raise TimeoutError

    def retry_task(self, task_uuid):
        task_runner.delay_task(self._eth_endpoint('retry_task'), {'task_uuid': task_uuid })

    def retry_failed(self, min_task_id, max_task_id, retry_unstarted):
        return self._execute_synchronous_celery(
            self._eth_endpoint('retry_failed'),
            {'min_task_id': min_task_id, 'max_task_id': max_task_id, 'retry_unstarted': retry_unstarted}
        )

    def deduplicate(self, min_task_id, max_task_id):
        return self._execute_synchronous_celery(
            self._eth_endpoint('deduplicate'), {'min_task_id': min_task_id, 'max_task_id': max_task_id}
        )

    def remove_prior_task_dependency(self, task_uuid, prior_task_uuid):
        return self._execute_synchronous_celery(
            self._eth_endpoint('remove_prior_task_dependency'),
            {'task_uuid': task_uuid, 'prior_task_uuid': prior_task_uuid}
        )

    def remove_all_posterior_dependencies(self, prior_task_uuid):
        return self._execute_synchronous_celery(
            self._eth_endpoint('remove_all_posterior_dependencies'),
            {'prior_task_uuid': prior_task_uuid}
        )

    # TODO: dynamically set topups according to current app gas price (currently at 2 gwei)
    def create_blockchain_wallet(
            self, wei_target_balance=2e16, wei_topup_threshold=1e16, private_key=None, queue='high-priority'
    ):
        """
        Creates a blockchain wallet on the blockchain worker
        :param wei_target_balance: How much eth to top the wallet's balance up to
        :param wei_topup_threshold: How low the wallet's balance should drop before attempting a topup
        :param private_key:
        :return: The wallet's address
        """
        args={
            'wei_target_balance': wei_target_balance,
            'wei_topup_threshold': wei_topup_threshold,
            'private_key': private_key
        }
        wallet_address = self._execute_synchronous_celery(
            self._eth_endpoint('create_new_blockchain_wallet'), args, queue=queue
        )

        if wei_target_balance or 0 > 0:
            self.topup_wallet_if_required(wallet_address, queue=queue)

        return wallet_address

    def send_eth(self, signing_address, recipient_address, amount_wei, prior_tasks=None):
        """
        Send eth to a target address
        :param signing_address: blockchain address of the txn signer/sender
        :param recipient_address: blockchain address of the recipent
        :param amount_wei: amount of eth to send, in wei
        :param prior_tasks: tasks that must successfully complete first befotehand
        :return: task uuid
        """
        kwargs={
            'signing_address': signing_address,
            'amount_wei': amount_wei,
            'recipient_address': recipient_address,
            'prior_tasks': prior_tasks
        }
        return task_runner.delay_task(self._eth_endpoint('send_eth'), kwargs).id

    def deploy_contract(
            self,
            signing_address: str,
            contract_name: str,
            constructor_args: Optional[List] = None,
            constructor_kwargs: Optional[Dict] = None,
            prior_tasks: Optional[List[int]] = None) -> int:
        kwargs={
            'signing_address': signing_address,
            'contract_name': contract_name,
            'args': constructor_args,
            'kwargs': constructor_kwargs,
            'prior_tasks': prior_tasks
        }
        return task_runner.delay_task(self._eth_endpoint('deploy_contract'), kwargs)

    def make_token_transfer(self, signing_address, token,
                            from_address, to_address, amount,
                            prior_tasks=None,
                            queue='high-priority',
                            task_uuid=None):
        """
        Makes a "Transfer" or "Transfer From" transaction on an ERC20 token.

        :param signing_address: address of wallet signing txn
        :param token: ERC20 token being transferred
        :param from_address: address of wallet sending token
        :param to_address:
        :param amount: the CENTS amount being sent, eg 2300 Cents = 2.3 Dollars
        :param prior_tasks: list of task uuids that must complete before txn will attempt
        :return: task uuid for the transfer
        """
        raw_amount = token.system_amount_to_token(amount, queue=queue)
        if signing_address == from_address:
            return self._transaction_task(
                signing_address=signing_address,
                contract_address=token.address,
                contract_type='ERC20',
                func='transfer',
                args=[
                    to_address,
                    raw_amount
                ],
                prior_tasks=prior_tasks,
                queue=queue,
                task_uuid=task_uuid
            )

        return self._transaction_task(
            signing_address=signing_address,
            contract_address=token.address,
            contract_type='ERC20',
            func='transferFrom',
            args=[
                from_address,
                to_address,
                token.system_amount_to_token(amount, queue)
            ],
            prior_tasks=prior_tasks,
            queue=queue,
            task_uuid=task_uuid
        )

    def make_approval(self,
                      signing_address, token,
                      spender, amount,
                      prior_tasks=None):

        # TODO: Fix the signature on this

        return self._transaction_task(
            signing_address=signing_address,
            contract_address=token.address,
            contract_type='ERC20',
            func='approve',
            gas_limit=100000,
            args=[
                spender,
                int(1e36)
            ],
            prior_tasks=prior_tasks
        )

    def make_liquid_token_exchange(self,
                                   signing_address,
                                   exchange_contract,
                                   from_token,
                                   to_token,
                                   reserve_token,
                                   from_amount,
                                   prior_tasks=None,
                                   task_uuid=None):
        """
        Uses a Liquid Token Contract network to exchange between two ERC20 smart tokens.
        :param signing_address: address of wallet signing txn
        :param exchange_contract: the base convert contract used in the network
        :param from_token: the token being exchanged from
        :param to_token: the token being exchanged to
        :param reserve_token: the reserve token used as a connector in the network
        :param from_amount: the amount of the token being exchanged from
        :param prior_tasks: list of task uuids that must complete before txn will attempt
        :return: task uuid for the exchange
        """
        prior_tasks = prior_tasks or []

        path = self._get_path(from_token, to_token, reserve_token)
        #
        # topup_task_uuid = self.topup_wallet_if_required(signing_address)
        #
        # if topup_task_uuid:
        #     prior_tasks.append(topup_task_uuid)

        return self._transaction_task(
            signing_address=signing_address,
            contract_address=exchange_contract.blockchain_address,
            contract_type='bancor_converter',
            func='quickConvert',
            args=[
                path,
                from_token.system_amount_to_token(from_amount),
                1
            ],
            prior_tasks=prior_tasks,
            task_uuid=task_uuid
        )

    def get_conversion_amount(self, exchange_contract, from_token, to_token, from_amount, signing_address=None):
        """
        Estimates the conversion amount received from a Liquid Token Contract network
        :param exchange_contract: the base convert contract used in the network
        :param from_token: the token being exchanged from
        :param to_token: the token being exchanged to
        :param from_amount: the amount of the token being exchanged from
        """

        def get_token_exchange_details(token):
            subexchange_details = exchange_contract.get_subexchange_details(token.address)
            subexchange_address = subexchange_details['subexchange_address']

            token_supply = self._synchronous_call(
                contract_address=token.address,
                contract_type='ERC20',
                func='totalSupply'
            )

            subexchange_reserve = self._synchronous_call(
                contract_address=reserve_token.address,
                contract_type='ERC20',
                func='balanceOf',
                args=[subexchange_address]
            )

            subexchange_reserve_ratio_ppm = subexchange_details['subexchange_reserve_ratio_ppm']

            return token_supply, subexchange_reserve, subexchange_reserve_ratio_ppm

        raw_from_amount = from_token.system_amount_to_token(from_amount)

        reserve_token = exchange_contract.reserve_token

        from_is_reserve = from_token == reserve_token
        to_is_reserve = to_token == reserve_token

        if (not from_is_reserve) and (not to_is_reserve):

            (from_token_supply,
             from_subexchange_reserve,
             from_subexchange_reserve_ratio_ppm) = get_token_exchange_details(from_token)

            (to_token_supply,
             to_subexchange_reserve,
             to_subexchange_reserve_ratio_ppm) = get_token_exchange_details(to_token)

            to_amount = bonding_curve_token1_to_token2(from_token_supply, to_token_supply,
                                                       from_subexchange_reserve, to_subexchange_reserve,
                                                       from_subexchange_reserve_ratio_ppm,
                                                       to_subexchange_reserve_ratio_ppm,
                                                       raw_from_amount)

        elif not from_is_reserve:
            (from_token_supply,
             from_subexchange_reserve,
             from_subexchange_reserve_ratio_ppm) = get_token_exchange_details(from_token)

            to_amount = bonding_curve_tokens_to_reserve(from_token_supply,
                                                        from_subexchange_reserve,
                                                        from_subexchange_reserve_ratio_ppm,
                                                        raw_from_amount)

        else:
            (to_token_supply,
             to_subexchange_reserve,
             to_subexchange_reserve_ratio_ppm) = get_token_exchange_details(to_token)

            to_amount = bonding_curve_reserve_to_tokens(to_token_supply,
                                                        to_subexchange_reserve,
                                                        to_subexchange_reserve_ratio_ppm,
                                                        raw_from_amount)

        to_amount = round(to_amount)

        return to_token.token_amount_to_system(to_amount)

    def _get_path(self, from_token, to_token, reserve_token):

        if from_token == reserve_token:
            return[
                reserve_token.address,
                to_token.address,
                to_token.address
            ]

        elif to_token == reserve_token:
            return [
                from_token.address,
                from_token.address,
                reserve_token.address,
            ]

        else:
            return [
                from_token.address,
                from_token.address,
                reserve_token.address,
                to_token.address,
                to_token.address
            ]

    def get_token_decimals(self, token, queue='high-priority'):
        return self._synchronous_call(
            contract_address=token.address,
            contract_type='ERC20',
            func='decimals',
            queue=queue
        )

    def get_wallet_balance(self, address, token, queue='high-priority'):

        balance_wei = self._synchronous_call(
            contract_address=token.address,
            contract_type='ERC20',
            func='balanceOf',
            args=[address],
            queue=queue)

        return balance_wei

    def get_allowance(self, token, owner_address, spender_address):

        allowance_wei = self._synchronous_call(
            contract_address=token.address,
            contract_type='ERC20',
            func='allowance',
            args=[owner_address, spender_address])

        return allowance_wei

    def deploy_exchange_network(self, deploying_address):
        """
        Deploys the underlying set of contracts required to set up a network of exchanges
        :param deploying_address: The address of the wallet used to deploy the network
        :return: registry contract address
        """
        return self._execute_synchronous_celery(
            self._eth_endpoint('deploy_exchange_network'),
            args=[deploying_address],
            timeout=current_app.config['CHAINS'][get_chain()]['SYNCRONOUS_TASK_TIMEOUT'] * 25
        )

    def deploy_and_fund_reserve_token(self, deploying_address, name, symbol, fund_amount_wei):
        args = [deploying_address, name, symbol, fund_amount_wei]
        return self._execute_synchronous_celery(
            self._eth_endpoint('deploy_and_fund_reserve_token'),
            args=args,
            timeout=current_app.config['CHAINS'][get_chain()]['SYNCRONOUS_TASK_TIMEOUT'] * 20
        )

    def deploy_smart_token(self,
                           deploying_address,
                           name, symbol, decimals,
                           reserve_deposit_wei,
                           issue_amount_wei,
                           contract_registry_address,
                           reserve_token_address,
                           reserve_ratio_ppm):

        args=[deploying_address,
              name, symbol, decimals,
              int(reserve_deposit_wei),
              int(issue_amount_wei),
              contract_registry_address,
              reserve_token_address,
              int(reserve_ratio_ppm)]

        return self._execute_synchronous_celery(
            self._eth_endpoint('deploy_smart_token'),
            args=args,
            timeout=current_app.config['CHAINS'][get_chain()]['SYNCRONOUS_TASK_TIMEOUT'] * 15
        )

    def topup_wallet_if_required(self, wallet_address, queue='high-priority'):
        return self._execute_synchronous_celery(
            self._eth_endpoint('topup_wallet_if_required'),
            args=[wallet_address],
            queue=queue
        )

