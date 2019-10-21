from server import db

from server.models.utils import (
    ModelBase,
    exchange_contract_token_association_table
)

import server.models.credit_transfer

from server.utils.blockchain_tasks import make_liquid_token_exchange, get_conversion_amount

from server.utils.transfer_account import find_transfer_accounts_with_matching_token

class ExchangeContract(ModelBase):
    __tablename__ = 'exchange_contract'

    blockchain_address = db.Column(db.String())

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

    def exchange_from_amount(self, user, from_token, to_token, from_amount):

        self.user = user
        self.from_token = from_token
        self.to_token = to_token

        # TODO: get this to work as an actual SQLAlchemy Filter
        exchange_contracts = ExchangeContract.query.all()
        exchange_contract = None
        for c in exchange_contracts:
            if (from_token in c.exchangeable_tokens) and (to_token in c.exchangeable_tokens):
                exchange_contract = c

        if exchange_contract is None:
            raise Exception("No matching exchange contract found")

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

    def exchange_to_desired_amount(self, to_desired_amount):
        """
        This is 'to_desired_amount' rather than just 'to_amount'
        because we can't actually guarantee how much of the 'to' token the user will receive through the exchange
        """
        pass

    # credit_sends = db.relationship('CreditTransfer', backref='sender_user',
    #                                lazy='dynamic', foreign_keys='CreditTransfer.inbound_')
    #
    # credit_receives = db.relationship('CreditTransfer', backref='recipient_user',
    #                                   lazy='dynamic', foreign_keys='CreditTransfer.recipient_user_id')

