import datetime
from sqlalchemy.sql import func
from flask import current_app
from sqlalchemy.ext.hybrid import hybrid_property
from server import db
from server.models.utils import ModelBase, OneOrgBase, user_transfer_account_association_table
from server.models.user import User
from server.models.spend_approval import SpendApproval
from server.models.exchange import ExchangeContract
import server.models.credit_transfer
from server.models.blockchain_transaction import BlockchainTransaction
from server.utils.blockchain_tasks import (
    create_blockchain_wallet
)
from server.utils.transfer_enums import TransferStatusEnum


class TransferAccount(OneOrgBase, ModelBase):
    __tablename__ = 'transfer_account'

    name            = db.Column(db.String())
    balance         = db.Column(db.BigInteger, default=0)
    blockchain_address = db.Column(db.String())

    is_approved     = db.Column(db.Boolean, default=False)

    # These are different from the permissions on the user:
    # is_vendor determines whether the account is allowed to have cash out operations etc
    # is_beneficiary determines whether the account is included in disbursement lists etc
    is_vendor       = db.Column(db.Boolean, default=False)

    is_beneficiary = db.Column(db.Boolean, default=False)

    payable_period_type   = db.Column(db.String(), default='week')
    payable_period_length = db.Column(db.Integer, default=2)
    payable_epoch         = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    token_id        = db.Column(db.Integer, db.ForeignKey("token.id"))

    exchange_contract_id = db.Column(db.Integer, db.ForeignKey(ExchangeContract.id))

    transfer_card    = db.relationship('TransferCard', backref='transfer_account', lazy=True, uselist=False)

    # users               = db.relationship('User', backref='transfer_account', lazy=True)
    users = db.relationship(
        "User",
        secondary=user_transfer_account_association_table,
        back_populates="transfer_accounts")

    # owning_organisation_id = db.Column(db.Integer, db.ForeignKey(Organisation.id))

    # owning_organisation = db.relationship("Organsisation", backref='org_level_transfer_account',
    #                                       lazy='dynamic', foreign_keys=Organisation.org_level_transfer_account_id)

    # blockchain_address = db.relationship('BlockchainAddress', backref='transfer_account', lazy=True, uselist=False)

    credit_sends       = db.relationship('CreditTransfer', backref='sender_transfer_account',
                                         lazy='dynamic', foreign_keys='CreditTransfer.sender_transfer_account_id')

    credit_receives    = db.relationship('CreditTransfer', backref='recipient_transfer_account',
                                         lazy='dynamic', foreign_keys='CreditTransfer.recipient_transfer_account_id')

    spend_approvals_given = db.relationship('SpendApproval', backref='giving_transfer_account',
                                            lazy='dynamic', foreign_keys='SpendApproval.giving_transfer_account_id')

    def add_to_balance(self, amount):

        if not self.balance:
            self.balance = amount
        else:
            self.balance += amount

    def get_or_create_system_transfer_approval(self):

        organisation_blockchain_address = self.organisation.system_blockchain_address

        approval = self.get_approval(organisation_blockchain_address)

        if not approval:
            approval = self.give_approval_to_address(organisation_blockchain_address)

        return approval

    def give_approval_to_address(self, address_getting_approved):
        approval = SpendApproval(transfer_account_giving_approval=self,
                                 address_getting_approved=address_getting_approved)
        return approval

    def get_approval(self, receiving_address):
        for approval in self.spend_approvals_given:
            if approval.receiving_address == receiving_address:
                return approval
        return None

    @hybrid_property
    def total_sent(self):
        return int(
            db.session.query(func.sum(server.models.credit_transfer.CreditTransfer.transfer_amount).label('total')).execution_options(show_all=True)
            .filter(server.models.credit_transfer.CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE)
            .filter(server.models.credit_transfer.CreditTransfer.sender_transfer_account_id == self.id).first().total or 0
        )

    @hybrid_property
    def total_received(self):
        return int(
            db.session.query(func.sum(server.models.credit_transfer.CreditTransfer.transfer_amount).label('total')).execution_options(show_all=True)
            .filter(server.models.credit_transfer.CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE)
            .filter(server.models.credit_transfer.CreditTransfer.recipient_transfer_account_id == self.id).first().total or 0
        )

    # @hybrid_property
    # def balance(self):
    #     return self.total_received - self.total_sent

    @hybrid_property
    def primary_user(self):
        users = User.query.execution_options(show_all=True) \
            .filter(User.transfer_accounts.any(TransferAccount.id.in_([self.id]))).all()
        if len(users) == 0:
            # This only happens when we've unbound a user from a transfer account by manually editing the db
            return None

        return sorted(users, key=lambda user: user.created)[0]

    @hybrid_property
    def primary_user_id(self):
        return self.primary_user.id

    @hybrid_property
    def master_wallet_approval_status(self):

        if not current_app.config['USING_EXTERNAL_ERC20']:
            return 'NOT_REQUIRED'

        if not self.blockchain_address.encoded_private_key:
            return 'NOT_REQUIRED'

        base_query = (
            BlockchainTransaction.query
                .filter(BlockchainTransaction.transaction_type == 'master wallet approval')
                .filter(BlockchainTransaction.credit_transfer.has(recipient_transfer_account_id=self.id))
        )

        successful_transactions = base_query.filter(BlockchainTransaction.status == 'SUCCESS').all()

        if len(successful_transactions) > 0:
            return 'APPROVED'

        requested_transactions = base_query.filter(BlockchainTransaction.status == 'PENDING').all()

        if len(requested_transactions) > 0:
            return 'REQUESTED'

        failed_transactions = base_query.filter(BlockchainTransaction.status == 'FAILED').all()

        if len(failed_transactions) > 0:
            return 'FAILED'

        return 'NO_REQUEST'

    def approve(self):

        if not self.is_approved:
            self.is_approved = True

            if self.is_beneficiary:
                disbursement = self.make_initial_disbursement()
                return disbursement

    def make_initial_disbursement(self, initial_balance=None):
        from server.utils.credit_transfers import make_disbursement_transfer
        if not initial_balance:
            initial_balance = current_app.config['STARTING_BALANCE']

        disbursement = make_disbursement_transfer(initial_balance, self)

        return disbursement

    def initialise_withdrawal(self, withdrawal_amount):
        from server.utils.credit_transfers import make_withdrawal_transfer
        withdrawal = make_withdrawal_transfer(withdrawal_amount,
                                              send_account=self,
                                              automatically_resolve_complete=False)
        return withdrawal

    def __init__(self, blockchain_address=None, organisation=None, **kwargs):
        super(TransferAccount, self).__init__(**kwargs)

        # blockchain_address_obj = BlockchainAddress(type="TRANSFER_ACCOUNT", blockchain_address=blockchain_address)
        # db.session.add(blockchain_address_obj)

        self.blockchain_address = blockchain_address or create_blockchain_wallet()

        if organisation:
            self.organisation = organisation
            self.token = organisation.token
