from functools import partial
from server import db

from server.models.utils import (
    ModelBase,
    BlockchainTaskableBase,
    exchange_contract_token_association_table
)

import server.models.credit_transfer
import server.models.transfer_account

from server.utils.blockchain_tasks import (
    make_liquid_token_exchange,
    make_approval,
    get_conversion_amount,
    get_wallet_balance
)

from server.utils.transfer_account import find_transfer_accounts_with_matching_token
from server.utils.root_solver import find_monotonic_increasing_bounds, false_position_method

from server.exceptions import InsufficientBalanceError


class ExchangeContract(ModelBase):
    __tablename__ = 'exchange_contract'

    blockchain_address = db.Column(db.String(), index=True)

    reserve_token_id = db.Column(db.Integer, db.ForeignKey("token.id"))

    exchangeable_tokens = db.relationship(
        "Token",
        secondary=exchange_contract_token_association_table,
        back_populates="exchange_contracts")

    transfer_accounts = db.relationship(
        'TransferAccount', backref='exchange_contract',
        lazy=True, foreign_keys='TransferAccount.exchange_contract_id'
    )

    def add_token(self, token):

        exchange_transfer_account = (server.models.transfer_account.TransferAccount.query
                                     .filter_by(token=token)
                                     .filter_by(exchange_contract=self)
                                     .first())

        if not exchange_transfer_account:
            exchange_transfer_account = server.models.transfer_account.TransferAccount(
                blockchain_address=self.blockchain_address,
                is_public=True
            )

            exchange_transfer_account.token = token
            db.session.add(exchange_transfer_account)

        exchange_transfer_account.exchange_contract = self

        self.exchangeable_tokens.append(token)

    def __init__(self, blockchain_address):

        self.blockchain_address = blockchain_address


class Exchange(BlockchainTaskableBase):
    __tablename__ = 'exchange'

    to_desired_amount = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

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

        if calculated_to_amount:
            to_amount = calculated_to_amount
        else:
            # TODO: Shift this away from an estimate to getting the real number async from the completed task
            to_amount = get_conversion_amount(exchange_contract.blockchain_address,
                                              from_token,
                                              to_token,
                                              exchange_contract.reserve_token,
                                              from_amount)

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

        self.to_transfer = server.models.credit_transfer.CreditTransfer(
            to_amount,
            to_token,
            sender_transfer_account=find_transfer_accounts_with_matching_token(exchange_contract, to_token),
            recipient_user=user)

        db.session.add(self.to_transfer)

        self.from_transfer.resolve_as_completed(existing_blockchain_txn=True)
        self.to_transfer.resolve_as_completed(existing_blockchain_txn=True)

        # We need to approve all the tokens involved for spend by the exchange contract
        to_approval_id = make_approval(
            signing_address=self.from_transfer.sender_transfer_account.blockchain_address,
            token=to_token,
            spender=exchange_contract.blockchain_address,
            amount=from_amount * 100000
        )

        reserve_approval_id = make_approval(
            signing_address=self.from_transfer.sender_transfer_account.blockchain_address,
            token=exchange_contract.reserve_token,
            spender=exchange_contract.blockchain_address,
            amount=from_amount * 100000
        )

        from_approval_id = make_approval(
            signing_address=self.from_transfer.sender_transfer_account.blockchain_address,
            token=from_token,
            spender=exchange_contract.blockchain_address,
            amount=from_amount*100000
        )

        task_id = make_liquid_token_exchange(
            signing_address=self.from_transfer.sender_transfer_account.blockchain_address,
            exchange_contract_address=exchange_contract.blockchain_address,
            from_token=from_token,
            to_token=to_token,
            reserve_token=exchange_contract.reserve_token,
            from_amount=from_amount,
            dependent_on_tasks=[to_approval_id, reserve_approval_id, from_approval_id]
        )

        self.blockchain_task_id = task_id
        self.from_transfer.blockchain_task_id = task_id
        self.to_transfer.blockchain_task_id = task_id

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
            get_conversion_amount,
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
