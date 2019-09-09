

class UnmintableERC20Processor(BaseERC20Processor):

    def make_disbursement(self,
                          transfer_amount,
                          recipient_address,
                          account_to_approve_encoded_pk,
                          master_wallet_approval_status,
                          uncompleted_tasks,
                          is_retry,
                          credit_transfer_id=None):

        chain_list = []

        approval_required = self.determine_if_master_wallet_approval_required(
            master_wallet_approval_status,
            uncompleted_tasks,
            is_retry)

        if approval_required:
            chain_list.extend(
                self.construct_master_wallet_approval_tasks(
                    account_to_approve_encoded_pk,
                    credit_transfer_id)
            )

        if not is_retry or 'disbursement' in uncompleted_tasks:
            chain_list.extend([
                celery_tasks.disburse_funds.si(transfer_amount, recipient_address, credit_transfer_id),
                celery_tasks.check_transaction_response.s(credit_transfer_id)
            ])


        if not is_retry or 'ether load' in uncompleted_tasks:
            if float(self.force_eth_disbursement_amount or 0) > 0:

                forced_amount_wei = Web3.toWei(self.force_eth_disbursement_amount, 'ether')

                chain_list.extend([
                    celery_tasks.load_ether.si(recipient_address, forced_amount_wei, 1),
                    celery_tasks.check_transaction_response.s(credit_transfer_id)
                ])

        chain(chain_list).on_error(celery_tasks.log_error.s(credit_transfer_id)).delay()

    def make_payment(self,
                     transfer_amount,
                     sender_address,
                     recipient_address,
                     account_to_approve_encoded_pk,
                     master_wallet_approval_status,
                     uncompleted_tasks,
                     is_retry,
                     credit_transfer_id=None):

        chain_list = []

        approval_required = self.determine_if_master_wallet_approval_required(
            master_wallet_approval_status,
            uncompleted_tasks,
            is_retry)

        if approval_required:
            chain_list.extend(
                self.construct_master_wallet_approval_tasks(
                    account_to_approve_encoded_pk,
                    credit_transfer_id)
            )


        if not is_retry or 'transfer' in uncompleted_tasks:
            chain_list.extend([
                celery_tasks.transfer_credit.si(transfer_amount, sender_address, recipient_address, credit_transfer_id),
                celery_tasks.check_transaction_response.s(credit_transfer_id),
            ])

        chain(chain_list).on_error(celery_tasks.log_error.s(credit_transfer_id)).delay()


    def make_withdrawal(self,
                        transfer_amount,
                        sender_address,
                        recipient_address,
                        account_to_approve_encoded_pk,
                        master_wallet_approval_status,
                        uncompleted_tasks,
                        is_retry,
                        credit_transfer_id=None):

        chain_list = []

        approval_required = self.determine_if_master_wallet_approval_required(
            master_wallet_approval_status,
            uncompleted_tasks,
            is_retry)

        if approval_required:
            chain_list.extend(
                self.construct_master_wallet_approval_tasks(
                    account_to_approve_encoded_pk,
                    credit_transfer_id)
            )

        if not is_retry or 'transfer' in uncompleted_tasks:

            chain_list.extend([
                celery_tasks.make_withdrawal.si(transfer_amount, sender_address, recipient_address, credit_transfer_id),
                celery_tasks.check_transaction_response.s(credit_transfer_id),
            ])

        chain(chain_list).on_error(celery_tasks.log_error.s(credit_transfer_id)).delay()

    def construct_master_wallet_approval_tasks(self, account_to_approve_encoded_pk, credit_transfer_id):

        private_key = self.decode_private_key(account_to_approve_encoded_pk)

        address = Web3.toChecksumAddress(utils.privtoaddr(private_key))

        gas_required, gas_price = self.estimate_load_ether_gas_and_price()

        return [
            celery_tasks.load_ether.si(address, gas_required, gas_price),
            celery_tasks.check_transaction_response.s(credit_transfer_id),
            celery_tasks.approve_master_for_transfers.si(account_to_approve_encoded_pk, gas_required, gas_price),
            celery_tasks.check_transaction_response.s(credit_transfer_id)
        ]

    def determine_if_master_wallet_approval_required(self, master_wallet_approval_status, uncompleted_tasks, is_retry):
        if master_wallet_approval_status in ['NO_REQUEST', 'FAILED'] or (
            is_retry and 'master wallet approval' in uncompleted_tasks
        ):
            # If the account hasn't received a disbursement previously,
            # it needs to approve the master wallet for transfers

            return True

        return False

    def disburse_funds_async(self, transfer_amount, recipient_address, credit_transfer_id):

        converted_amount = self.cents_to_native_amount(transfer_amount)

        fund_disbursement_txn = self.contract.functions.transfer(
            recipient_address,
            converted_amount
        )

        fund_disbursement_result = self.process_transaction(self.master_wallet_private_key,
                                                            credit_transfer_id=credit_transfer_id,
                                                            unbuilt_transaction=fund_disbursement_txn,
                                                            transaction_type='disbursement')

        return fund_disbursement_result

    def generate_approval_txn(self):

        sender_address = utils.checksum_encode(self.master_wallet_address)

        approve_amount = self.cents_to_native_amount(10 ** 8)

        transfer_approval_txn = self.contract.functions.approve(sender_address, approve_amount)

        return transfer_approval_txn

    def estimate_load_ether_gas_and_price(self):

        estimated_gas_required = round(45665 * 1.05)

        # estimated_gas_required = round(self.generate_approval_txn().estimateGas() * 1.05)

        gas_price = self.get_gas_price()

        return estimated_gas_required, gas_price


    def load_ether_async(self, recipient_address, gas_required, gas_price):

        txn_dict = {
            'to': recipient_address,
            'value': gas_required * gas_price
        }

        ether_load_result = self.process_transaction(self.master_wallet_private_key,
                                                     partial_txn_dict=txn_dict,
                                                     transaction_type='ether load')

        return ether_load_result

    def approve_master_for_transfers_async(self, account_to_approve_encoded_pk, gas_required, gas_price):

        private_key = self.decode_private_key(account_to_approve_encoded_pk)

        transfer_approval_txn = self.generate_approval_txn()

        approval_result = self.process_transaction(private_key,
                                                   unbuilt_transaction=transfer_approval_txn,
                                                   transaction_type='master wallet approval',
                                                   gas_limit_override= gas_required,
                                                   gas_price_override= gas_price
                                                   )

        return approval_result


    def transfer_credit_async(self,transfer_amount, sender_address, recipient_address, credit_transfer_id):

        converted_amount = self.zero_balance_compensated_cents_to_native_amount(transfer_amount, sender_address)

        txn = self.contract.functions.transferFrom(sender_address, recipient_address, converted_amount)

        return self.process_transaction(self.master_wallet_private_key,
                                        credit_transfer_id = credit_transfer_id,
                                        unbuilt_transaction=txn,
                                        transaction_type='transfer')

    def withdrawal_async(self,transfer_amount, sender_address, recipient_address, credit_transfer_id):

        converted_amount = self.zero_balance_compensated_cents_to_native_amount(transfer_amount, sender_address)

        if self.withdraw_to_address:
            recipient_address = self.withdraw_to_address
        else:
            recipient_address = self.master_wallet_address

        txn = self.contract.functions.transferFrom(sender_address, recipient_address, converted_amount)

        return self.process_transaction(self.master_wallet_private_key,
                                        credit_transfer_id=credit_transfer_id,
                                        unbuilt_transaction=txn,
                                        transaction_type='transfer')


    def get_master_wallet_balance_async(self):

        native_amount_balance = self.contract.functions.balanceOf(self.master_wallet_address).call()

        return self.native_amount_to_cents(native_amount_balance)

    def get_transfer_account_blockchain_addresses(self):

        r = requests.get(config.APP_HOST + '/api/blockchain_address/?filter=vendor',
                         auth=HTTPBasicAuth(config.BASIC_AUTH_USERNAME,
                                            config.BASIC_AUTH_PASSWORD))

        print('response:' + str(r))

        if r.status_code < 400:

            address_dict_list = r.json()['data']['blockchain_addresses']

            return [address_dict['address'] for address_dict in address_dict_list]
        else:
            return []


    def find_new_external_inbounds(self):

        address_list = self.get_transfer_account_blockchain_addresses()

        try:
            latest_block = self.wsw3.eth.getBlock('latest')

            threshold = latest_block.number - 2

            inbound_filter = self.websocket_contract.events.Transfer.createFilter(
                fromBlock=threshold,
                argument_filters={'dst': address_list})


            for event in inbound_filter.get_all_entries():

                try:

                    converted_amount = self.native_amount_to_cents(event['args']['wad'])

                    body = {
                        'sender_blockchain_address': event['args']['src'],
                        'recipient_blockchain_address': event['args']['dst'],
                        'blockchain_transaction_hash': event['transactionHash'].hex(),
                        'transfer_amount': converted_amount
                    }

                    r = requests.post(config.APP_HOST + '/api/credit_transfer/internal/',
                                      json=body,
                                      auth=HTTPBasicAuth(config.BASIC_AUTH_USERNAME,
                                                         config.BASIC_AUTH_PASSWORD))
                except KeyError:
                    pass

        except ssl.SSLError as e:
            pass


    def __init__(self,
                 contract_address,
                 contract_abi_string,
                 ethereum_chain_id,
                 http_provider,
                 websocket_provider,
                 gas_price_gwei,
                 gas_limit,
                 master_wallet_private_key,
                 force_eth_disbursement_amount=None,
                 withdraw_to_address = None):

        super(UnmintableERC20Processor, self).__init__(contract_address,
                                                       contract_abi_string,
                                                       ethereum_chain_id,
                                                       http_provider,
                                                       websocket_provider,
                                                       gas_price_gwei,
                                                       gas_limit)

        self.master_wallet_private_key = master_wallet_private_key
        self.master_wallet_address = Web3.toChecksumAddress(utils.privtoaddr(self.master_wallet_private_key))
        print('master wallet address: ' + self.master_wallet_address)

        self.websocket_contract = self.wsw3.eth.contract(address=self.contract_address, abi=self.abi_dict)

        self.force_eth_disbursement_amount = force_eth_disbursement_amount

        self.withdraw_to_address = withdraw_to_address
