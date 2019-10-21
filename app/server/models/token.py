from server import db
from server.utils.blockchain_tasks import (
    get_token_decimals,
)

from server.models.utils import (
    ModelBase,
    exchange_contract_token_association_table
)

from server.models.exchange import ExchangeContract
import server.models.transfer_account

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
        return int(float(system_amount) * 10**self.decimals / 100)

    def add_exchange_contract(self, exchange_contract: ExchangeContract):

        exchange_transfer_account = (server.models.transfer_account.TransferAccount.query
                                     .filter_by(token=self)
                                     .filter_by(exchange_contract=exchange_contract)
                                     .first())

        if not exchange_transfer_account:
            exchange_transfer_account = server.models.transfer_account.TransferAccount(
                blockchain_address=exchange_contract.blockchain_address,
                is_public=True
            )

            exchange_transfer_account.token = self
            db.session.add(exchange_transfer_account)


        exchange_transfer_account.exchange_contract = exchange_contract

        self.exchange_contracts.append(exchange_contract)


