from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.attributes import flag_modified

from functools import partial
from flask import current_app

from server import db, bt

import server.models.credit_transfer
import server.models.transfer_account

from server.models.utils import (
    ModelBase,
    BlockchainTaskableBase,
    exchange_contract_token_association_table
)

from server.utils.transfer_account import find_transfer_accounts_with_matching_token
from server.utils.root_solver import find_monotonic_increasing_bounds, false_position_method
from server.exceptions import InsufficientBalanceError


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
            return None
        return self.subexchange_address_mapping.get(token_address, None)

    def _add_subexchange(self, token_address, subexchange_address, subexchange_reserve_ratio_ppm):
        if self.subexchange_address_mapping is None:
            self.subexchange_address_mapping = {}
        self.subexchange_address_mapping[token_address] = {
            'subexchange_address': subexchange_address,
            'subexchange_reserve_ratio_ppm': subexchange_reserve_ratio_ppm
        }

        flag_modified(self, "subexchange_address_mapping")
        db.session.add(self)

    def add_reserve_token(self, reserve_token):
        self.reserve_token = reserve_token
        self.add_token(reserve_token, None, None)

    def add_token(self, token, subexchange_address, subexchange_reserve_ratio):
        exchange_transfer_account = server.models.transfer_account.TransferAccount(bind_to_entity=self, token=token)
        db.session.add(exchange_transfer_account)

        if subexchange_address:
            self.exchangeable_tokens.append(token)
            self._add_subexchange(token.address, subexchange_address, subexchange_reserve_ratio)


class Exchange(BlockchainTaskableBase):
    __tablename__ = 'exchange'

    to_desired_amount = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    exchange_rate = db.Column(db.FLOAT)

    # user_transfer_account_id = db.Column(db.Integer, db.ForeignKey("transfer_account.id"))
    # transfer_account = relationship("TransferAccount", back_populates="exchanges")

    from_token_id = db.Column(db.Integer, db.ForeignKey("token.id"))
    to_token_id = db.Column(db.Integer, db.ForeignKey("token.id"))

    from_transfer_id = db.Column(db.Integer, db.ForeignKey("credit_transfer.id"))
    to_transfer_id = db.Column(db.Integer, db.ForeignKey("credit_transfer.id"))


    def exchange_from_amount(self, user, from_token, to_token, from_amount, calculated_to_amount=None):

        self.user = user
        self.from_token = from_token
        self.to_token = to_token

        exchange_contract = self._find_exchange_contract(from_token, to_token)

        self.from_transfer = server.models.credit_transfer.CreditTransfer(
            from_amount,
            from_token,
            sender_user=user,
            recipient_transfer_account=find_transfer_accounts_with_matching_token(exchange_contract, from_token))

        if not self.from_transfer.check_sender_has_sufficient_balance():
            message = "Sender {} has insufficient balance".format(user)
            self.from_transfer.resolve_as_rejected(message)

            raise InsufficientBalanceError(message)

        db.session.add(self.from_transfer)

        signing_address = self.from_transfer.sender_transfer_account.blockchain_address

        topup_task_id = bt.topup_wallet_if_required(signing_address)

        dependent = [topup_task_id] if topup_task_id else []

        # TODO: set these so they either only fire on the first use of the exchange, or entirely asyn
        # We need to approve all the tokens involved for spend by the exchange contract
        to_approval_id = bt.make_approval(
            signing_address=signing_address,
            token=to_token,
            spender=exchange_contract.blockchain_address,
            amount=from_amount * 100000,
            dependent_on_tasks=dependent
        )

        reserve_approval_id = bt.make_approval(
            signing_address=signing_address,
            token=exchange_contract.reserve_token,
            spender=exchange_contract.blockchain_address,
            amount=from_amount * 100000,
            dependent_on_tasks=dependent
        )

        from_approval_id = bt.make_approval(
            signing_address=signing_address,
            token=from_token,
            spender=exchange_contract.blockchain_address,
            amount=from_amount*100000,
            dependent_on_tasks=dependent
        )

        if calculated_to_amount:
            to_amount = calculated_to_amount
        else:
            to_amount = bt.get_conversion_amount(exchange_contract=exchange_contract,
                                              from_token=from_token,
                                              to_token=to_token,
                                              from_amount=from_amount,
                                              signing_address=signing_address)

        self.exchange_rate = to_amount/from_amount

        task_id = bt.make_liquid_token_exchange(
            signing_address=signing_address,
            exchange_contract=exchange_contract,
            from_token=from_token,
            to_token=to_token,
            reserve_token=exchange_contract.reserve_token,
            from_amount=from_amount,
            dependent_on_tasks=[to_approval_id, reserve_approval_id, from_approval_id]
        )

        self.to_transfer = server.models.credit_transfer.CreditTransfer(
            to_amount,
            to_token,
            sender_transfer_account=find_transfer_accounts_with_matching_token(exchange_contract, to_token),
            recipient_user=user)

        db.session.add(self.to_transfer)

        self.blockchain_task_id = task_id
        self.from_transfer.blockchain_task_id = task_id
        self.to_transfer.blockchain_task_id = task_id

        self.from_transfer.resolve_as_completed(existing_blockchain_txn=True)
        self.to_transfer.resolve_as_completed(existing_blockchain_txn=True)

    def exchange_to_desired_amount(self, user, from_token, to_token, to_desired_amount):
        """
        This is 'to_desired_amount' rather than just 'to_amount'
        because we can't actually guarantee how much of the 'to' token the user will receive through the exchange
        """
        from_amount, calculated_to_amount = self._estimate_from_amount(from_token, to_token, to_desired_amount)

        self.exchange_from_amount(user, from_token, to_token, from_amount, calculated_to_amount)

    def _find_exchange_contract(self, from_token, to_token):

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
