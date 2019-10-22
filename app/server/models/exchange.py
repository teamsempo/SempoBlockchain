from functools import partial
from server import db

from server.models.utils import (
    ModelBase,
    exchange_contract_token_association_table
)

import server.models.credit_transfer

from server.utils.blockchain_tasks import make_liquid_token_exchange, get_conversion_amount
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

    transfer_accounts = db.relationship('TransferAccount', backref='exchange_contract',
                                         lazy=True, foreign_keys='TransferAccount.exchange_contract_id')

    def __init__(self, blockchain_address):

        self.blockchain_address = blockchain_address


class Exchange(ModelBase):
    __tablename__ = 'exchange'

    to_desired_amount = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    # user_transfer_account_id = db.Column(db.Integer, db.ForeignKey("transfer_account.id"))
    # transfer_account = relationship("TransferAccount", back_populates="exchanges")

    from_token_id = db.Column(db.Integer, db.ForeignKey("token.id"))

    to_token_id = db.Column(db.Integer, db.ForeignKey("token.id"))

    from_transfer_id = db.Column(db.Integer, db.ForeignKey("credit_transfer.id"))

    to_transfer_id = db.Column(db.Integer, db.ForeignKey("credit_transfer.id"))

    blockchain_task_id = db.Column(db.Integer)


    def exchange_from_amount(self, user, from_token, to_token, from_amount, calculated_to_amount = None):

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

        task_id = make_liquid_token_exchange(signing_address=self.from_transfer.sender_transfer_account.blockchain_address,
                                             exchange_contract_address=exchange_contract.blockchain_address,
                                             from_token=from_token,
                                             to_token=to_token,
                                             reserve_token=exchange_contract.reserve_token,
                                             from_amount=from_amount)

        self.blockchain_task_id = task_id

    def exchange_to_desired_amount(self, user, from_token, to_token, to_desired_amount):
        """
        This is 'to_desired_amount' rather than just 'to_amount'
        because we can't actually guarantee how much of the 'to' token the user will receive through the exchange
        """
        from_amount, calculated_to_amount = self._estimate_from_amount(from_token, to_token, to_desired_amount)

        self.exchange_from_amount(user, from_token, to_token, from_amount, calculated_to_amount)

    def _find_exchange_contract(self, from_token, to_token):
        # TODO: get this to work as an actual SQLAlchemy Filter
        exchange_contracts = ExchangeContract.query.all()
        exchange_contract = None
        for c in exchange_contracts:
            if (from_token in c.exchangeable_tokens) and (to_token in c.exchangeable_tokens):
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
