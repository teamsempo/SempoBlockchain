import enum
from sqlalchemy import or_
from sqlalchemy.ext.hybrid import hybrid_property

from server import db, bt

from server.models.utils import (
    ModelBase,
    exchange_contract_token_association_table
)

class TokenType(enum.Enum):
    LIQUID      = 'LIQUID'
    RESERVE     = 'RESERVE'


class Token(ModelBase):
    __tablename__ = 'token'

    address = db.Column(db.String, index=True, unique=True, nullable=True)
    name = db.Column(db.String)
    symbol = db.Column(db.String)
    _decimals = db.Column(db.Integer)

    token_type = db.Column(db.Enum(TokenType))

    organisations = db.relationship('Organisation',
                                    backref='token',
                                    lazy=True,
                                    foreign_keys='Organisation.token_id')

    transfer_accounts = db.relationship('TransferAccount', backref='token', lazy=True,
                                         foreign_keys='TransferAccount.token_id')

    credit_transfers = db.relationship('CreditTransfer', backref='token', lazy=True,
                                        foreign_keys='CreditTransfer.token_id')

    approvals = db.relationship('SpendApproval', backref='token', lazy=True,
                                        foreign_keys='SpendApproval.token_id')

    reserve_for_exchange = db.relationship('ExchangeContract', backref='reserve_token', lazy=True,
                                           foreign_keys='ExchangeContract.reserve_token_id')

    exchange_contracts = db.relationship(
        "ExchangeContract",
        secondary=exchange_contract_token_association_table,
        back_populates="exchangeable_tokens")

    exchanges_from = db.relationship('Exchange', backref='from_token', lazy=True,
                                     foreign_keys='Exchange.from_token_id')

    exchanges_to = db.relationship('Exchange', backref='to_token', lazy=True,
                                   foreign_keys='Exchange.to_token_id')

    fiat_ramps = db.relationship('FiatRamp', backref='token', lazy=True,
                                 foreign_keys='FiatRamp.token_id')

    def get_decimals(self, queue='high-priority'):
        if self._decimals:
            return self._decimals
        decimals_from_contract_definition = bt.get_token_decimals(self, queue=queue)
        if decimals_from_contract_definition:
            self._decimals = decimals_from_contract_definition
            return decimals_from_contract_definition
        raise Exception("Decimals not defined in either database or contract")


    @hybrid_property
    def decimals(self):
        return self.get_decimals()

    @decimals.setter
    def decimals(self, value):
        self._decimals = value

    def token_amount_to_system(self, token_amount, queue='high-priority'):
        return int(token_amount) / 10**self.get_decimals(queue) * 100

    def system_amount_to_token(self, system_amount, queue='high-priority'):
        return int(float(system_amount)/100 * 10**self.get_decimals(queue))
