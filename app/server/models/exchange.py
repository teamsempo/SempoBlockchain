from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.attributes import flag_modified

from functools import partial
from flask import current_app, g
from uuid import uuid4

from server import db, bt

import server.models.credit_transfer
import server.models.transfer_account
from server.utils.transfer_enums import TransferTypeEnum

from server.models.utils import (
    ModelBase,
    BlockchainTaskableBase,
    exchange_contract_token_association_table
)

from server.utils.transfer_account import find_transfer_accounts_with_matching_token
from server.utils.root_solver import find_monotonic_increasing_bounds, false_position_method
from server.exceptions import InsufficientBalanceError, SubexchangeNotFound


class ExchangeContract(ModelBase):
    """
    class for tracking contracts used for making on-chain exchanges of tokens
    (rather than using an internal sempo blockchain account that holds and swaps multiple tokens)
    currently only supports exchanges using liquid token contracts, though could be extended to support
    a constant-product market maker, continuous-double auction DEX etc.

    @:param blockchain_address:
    The address to which exchange requests should be sent.
    @:param contract_registry_blockchain_address:
    The contract registry is used to add new liquid token sub-exchanges.
    @:param subexchange_address_mapping:
    Exchanges made using a liquid token don't use a single on-chain contract, but rather a network of
    exchange-contracts, one for each token that can be exchanged, which we label 'sub-exchanges'.
    Each one of these sub-exchanges includes an internal reserve-token balance, and has parameters defined
    such as the reserve-ratio.
    @:param reserve_token:
    The stable token used as the reserve for liquid tokens.
    @:param exchangeable_tokens:
    The tokens that are exchangable using this contract
    @:param transfer_accounts:
    Accounts used for tracking the sends and receives of the various tokens exchangable by the exchange-network
    """
    __tablename__ = 'exchange_contract'

    blockchain_address = db.Column(db.String(), index=True)

    contract_registry_blockchain_address = db.Column(db.String(), index=True)

    subexchange_address_mapping = db.Column(JSON)

    reserve_token_id = db.Column(db.Integer, db.ForeignKey("token.id"))

    exchangeable_tokens = db.relationship(
        "Token",
        secondary=exchange_contract_token_association_table,
        back_populates="exchange_contracts")

    transfer_accounts = db.relationship(
        'TransferAccount', backref='exchange_contract',
        lazy=True, foreign_keys='TransferAccount.exchange_contract_id'
    )

    def get_subexchange_details(self, token_address):
        if self.subexchange_address_mapping is None:
            raise SubexchangeNotFound

        details = self.subexchange_address_mapping.get(token_address, None)

        if not details:
            raise SubexchangeNotFound

        return details


    def _add_subexchange(self, token_address, subexchange_address, subexchange_reserve_ratio_ppm):
        if self.subexchange_address_mapping is None:
            self.subexchange_address_mapping = {}
        self.subexchange_address_mapping[token_address] = {
            'subexchange_address': subexchange_address,
            'subexchange_reserve_ratio_ppm': subexchange_reserve_ratio_ppm
        }

        if self.blockchain_address is None:
            self.blockchain_address = subexchange_address

        flag_modified(self, "subexchange_address_mapping")
        db.session.add(self)

    def add_reserve_token(self, reserve_token):
        self.reserve_token = reserve_token
        self.add_token(reserve_token, None, None)

    def add_token(self, token, subexchange_address, subexchange_reserve_ratio):

        exchange_transfer_account = (server.models.transfer_account.TransferAccount.query
                                     .filter_by(token=token)
                                     .filter_by(exchange_contract=self)
                                     .first())

        if not exchange_transfer_account:

            exchange_transfer_account = server.models.transfer_account.TransferAccount(
                bound_entity=self,
                token=token,
                is_approved=True)

            db.session.add(exchange_transfer_account)

        if subexchange_address:
            self.exchangeable_tokens.append(token)
            self._add_subexchange(token.address, subexchange_address, subexchange_reserve_ratio)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Exchange(BlockchainTaskableBase):
    __tablename__ = 'exchange'

    to_desired_amount = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    exchange_rate = db.Column(db.FLOAT)

    # user_transfer_account_id = db.Column(db.Integer, db.ForeignKey("transfer_account.id"))
    # transfer_account = relationship("TransferAccount", back_populates="exchanges")

    from_token_id = db.Column(db.Integer, db.ForeignKey("token.id"))
    to_token_id = db.Column(db.Integer, db.ForeignKey("token.id"))

    from_transfer_id = db.Column(db.Integer, db.ForeignKey("credit_transfer.id"), index=True)
    to_transfer_id = db.Column(db.Integer, db.ForeignKey("credit_transfer.id"), index=True)

    @staticmethod
    def get_exchange_rate(from_token, to_token):
        """
        eg if from USD to AUD, and 1 USD buys 2 AUD
        return AUD 2
        :param from_token:
        :param to_token:
        :return:
        """

        from_amount = 1

        exchange_contract = Exchange._find_exchange_contract(from_token, to_token)

        to_amount = bt.get_conversion_amount(
            exchange_contract=exchange_contract,
            from_token=from_token,
            to_token=to_token,
            from_amount=from_amount)

        return to_amount/from_amount

    def exchange_from_amount(
            self, user, from_token, to_token, from_amount, calculated_to_amount=None, prior_task_uuids=None,
            transfer_mode=None, queue='high-priority'
    ):
        self.user = user
        self.from_token = from_token
        self.to_token = to_token
        self.from_amount = from_amount

        self.exchange_contract = self._find_exchange_contract(from_token, to_token)

        self.from_transfer = server.models.credit_transfer.CreditTransfer(
            from_amount,
            from_token,
            sender_user=user,
            recipient_transfer_account=find_transfer_accounts_with_matching_token(self.exchange_contract, from_token),
            transfer_type=TransferTypeEnum.EXCHANGE,
            transfer_mode=transfer_mode
        )

        db.session.add(self.from_transfer)

        signing_address = self.from_transfer.sender_transfer_account.blockchain_address

        prior = []

        # TODO: set these so they either only fire on the first use of the exchange, or entirely asyn
        # We need to approve all the tokens involved for spend by the exchange contract
        self.to_approval_uuid = bt.make_approval(
            signing_address=signing_address,
            token=to_token,
            spender=self.exchange_contract.blockchain_address,
            amount=from_amount * 100000,
            prior_tasks=prior
        )

        self.reserve_approval_uuid = bt.make_approval(
            signing_address=signing_address,
            token=self.exchange_contract.reserve_token,
            spender=self.exchange_contract.blockchain_address,
            amount=from_amount * 100000,
            prior_tasks=prior
        )

        self.from_approval_uuid = bt.make_approval(
            signing_address=signing_address,
            token=from_token,
            spender=self.exchange_contract.blockchain_address,
            amount=from_amount*100000,
            prior_tasks=prior
        )

        if calculated_to_amount:
            to_amount = calculated_to_amount
        else:
            to_amount = bt.get_conversion_amount(exchange_contract=self.exchange_contract,
                                              from_token=from_token,
                                              to_token=to_token,
                                              from_amount=from_amount,
                                              signing_address=signing_address)

        self.exchange_rate = to_amount/from_amount

        self.blockchain_task_uuid = str(uuid4())
        g.pending_transactions.append((self, queue))

        self.to_transfer = server.models.credit_transfer.CreditTransfer(
            to_amount,
            to_token,
            sender_transfer_account=find_transfer_accounts_with_matching_token(self.exchange_contract, to_token),
            recipient_user=user,
            transfer_type=TransferTypeEnum.EXCHANGE,
            transfer_mode=transfer_mode,
            require_sufficient_balance=False
        )

        db.session.add(self.to_transfer)

        self.from_transfer.blockchain_task_uuid = self.blockchain_task_uuid
        self.to_transfer.blockchain_task_uuid = self.blockchain_task_uuid

        self.from_transfer.resolve_as_complete()
        self.to_transfer.resolve_as_complete()

    def send_blockchain_payload_to_worker(self, queue='high-priority'):
        return bt.make_liquid_token_exchange(
            signing_address=self.from_transfer.sender_transfer_account.blockchain_address,
            exchange_contract=self.exchange_contract,
            from_token=self.from_token,
            to_token=self.to_token,
            reserve_token=self.exchange_contract.reserve_token,
            from_amount=self.from_amount,
            prior_tasks=[self.to_approval_uuid, self.reserve_approval_uuid, self.from_approval_uuid],
            task_uuid=self.blockchain_task_uuid
        )

    def exchange_to_desired_amount(self, user, from_token, to_token, to_desired_amount, transfer_mode):
        """
        This is 'to_desired_amount' rather than just 'to_amount'
        because we can't actually guarantee how much of the 'to' token the user will receive through the exchange
        """
        from_amount, calculated_to_amount = self._estimate_from_amount(from_token, to_token, to_desired_amount)

        self.exchange_from_amount(user, from_token, to_token, from_amount, calculated_to_amount, transfer_mode)

    @staticmethod
    def _find_exchange_contract(from_token, to_token):

        def exchangeable_by_contract(token, contract):
            return token == contract.reserve_token or token in contract.exchangeable_tokens

        # TODO: get this to work as an actual SQLAlchemy Filter
        exchange_contracts = ExchangeContract.query.all()
        exchange_contract = None
        for c in exchange_contracts:
            if exchangeable_by_contract(from_token, c) and exchangeable_by_contract(to_token, c):
                exchange_contract = c

        if exchange_contract is None:
            raise Exception("No matching exchange contract found")

        return exchange_contract

    def _get_conversion_function(self, exchange_contract, from_token, to_token):
        return partial(
            bt.get_conversion_amount,
            exchange_contract.blockchain_address,
            from_token,
            to_token,
            exchange_contract.reserve_token
        )

    def _estimate_from_amount(self, from_token, to_token, to_desired_amount):
        max_error = 3e-15

        exchange_contract = self._find_exchange_contract(from_token, to_token)
        conversion_func = self._get_conversion_function(exchange_contract, from_token, to_token)

        def root_func(x):
            return conversion_func(x) - to_desired_amount

        x_lower, y_lower, x_upper, y_upper = find_monotonic_increasing_bounds(root_func, to_desired_amount)

        new_x, new_y = false_position_method(
            root_func,
            x_lower, y_lower,
            x_upper, y_upper,
            max_error, max_iterations=6)

        return new_x, new_y + to_desired_amount
