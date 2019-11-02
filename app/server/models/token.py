from server import db
from server.utils.blockchain_tasks import (
    get_token_decimals
)
from server.models.utils import ModelBase


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

    fiat_ramps = db.relationship('FiatRamp', backref='token', lazy=True,
                                 foreign_keys='FiatRamp.token_id')

    @property
    def decimals(self):
        if self._decimals:
            return self._decimals

        decimals_from_contract_definition = get_token_decimals(self)

        if decimals_from_contract_definition:
            return decimals_from_contract_definition

        raise Exception("Decimals not defined in either database or contract")

    def token_amount_to_system(self, token_amount):
        return int(token_amount) * 100 / 10**self.decimals

    def system_amount_to_token(self, system_amount):
        return int(float(system_amount) / 100 * 10**self.decimals)

