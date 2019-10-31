from sqlalchemy.ext.hybrid import hybrid_property
from flask import current_app
from server import db
from server.utils.blockchain_tasks import (
    get_token_decimals,
)

from server.models.utils import (
    ModelBase,
    exchange_contract_token_association_table
)

class Token(ModelBase):
    __tablename__ = 'token'

    address = db.Column(db.String, index=True, unique=True, nullable=False)
    name = db.Column(db.String)
    symbol = db.Column(db.String)
    _decimals = db.Column(db.Integer)

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

    @hybrid_property
    def decimals(self):
        if self._decimals:
            return self._decimals

        decimals_from_contract_definition = get_token_decimals(self)

        if decimals_from_contract_definition:
            return decimals_from_contract_definition

        raise Exception("Decimals not defined in either database or contract")

    @decimals.setter
    def decimals(self, value):
        self._decimals = value

    def token_amount_to_system(self, token_amount):
        return int(token_amount) * 100 / 10**self.decimals

    def system_amount_to_token(self, system_amount):
        return int(float(system_amount) * 10**self.decimals / 100)

    # def __init__(self, address, **kwargs):
    #     super(Token, self).__init__(**kwargs)
    #
    #     existing_token = Token.query.filter(Token.address == address).first()
    #
    #     if existing_token and not current_app.config.get('IS_PRODUCTION', True):
    #         # On non-product versions delete existing tokens.
    #         # This makes dev-ing way easier because you don't need to worry about clashed addresses
    #         db.session.delete(existing_token)
