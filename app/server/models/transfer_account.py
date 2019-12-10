from typing import Optional, Union
from decimal import Decimal
import datetime, enum
from sqlalchemy.sql import func
from flask import current_app
from sqlalchemy.ext.hybrid import hybrid_property
from server import db, bt
from server.models.utils import ModelBase, OneOrgBase, user_transfer_account_association_table
from server.models.user import User
from server.models.spend_approval import SpendApproval
from server.models.exchange import ExchangeContract
from server.models.organisation import Organisation
from server.models.token import Token
import server.models.credit_transfer
from server.models.blockchain_transaction import BlockchainTransaction

from server.utils.transfer_enums import TransferStatusEnum


class TransferAccountType(enum.Enum):
    USER            = 'USER'
    ORGANISATION    = 'ORGANISATION'
    FLOAT           = 'FLOAT'
    CONTRACT        = 'CONTRACT'


class TransferAccount(OneOrgBase, ModelBase):
    __tablename__ = 'transfer_account'

    name            = db.Column(db.String())
    _balance_wei    = db.Column(db.Numeric(27), default=0)
    blockchain_address = db.Column(db.String())

    is_approved     = db.Column(db.Boolean, default=False)

    # These are different from the permissions on the user:
    # is_vendor determines whether the account is allowed to have cash out operations etc
    # is_beneficiary determines whether the account is included in disbursement lists etc
    is_vendor       = db.Column(db.Boolean, default=False)

    is_beneficiary = db.Column(db.Boolean, default=False)

    is_ghost = db.Column(db.Boolean, default=False)

    account_type    = db.Column(db.Enum(TransferAccountType))

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
        back_populates="transfer_accounts"
    )

    credit_sends       = db.relationship('CreditTransfer', backref='sender_transfer_account',
                                         lazy='dynamic', foreign_keys='CreditTransfer.sender_transfer_account_id')

    credit_receives    = db.relationship('CreditTransfer', backref='recipient_transfer_account',
                                         lazy='dynamic', foreign_keys='CreditTransfer.recipient_transfer_account_id')

    spend_approvals_given = db.relationship('SpendApproval', backref='giving_transfer_account',
                                            lazy='dynamic', foreign_keys='SpendApproval.giving_transfer_account_id')

    def get_float_transfer_account(self):
        for transfer_account in self.organisation.transfer_accounts:
            if transfer_account.account_type == 'FLOAT':
                return transfer_account

        float_wallet = TransferAccount.query.filter(TransferAccount.account_type == TransferAccountType.FLOAT).first()

        return float_wallet

    @property
    def balance(self):
        # division/multipication by int(1e16) occurs  because
        # the db stores amounts in integer WEI: 1 BASE-UNIT (ETH/USD/ETC) * 10^18
        # while the system passes around amounts in float CENTS: 1 BASE-UNIT (ETH/USD/ETC) * 10^2
        # Therefore the conversion between db and system is 10^18/10^2c = 10^16
        # We use cents for historical reasons, and to enable graceful degredation/rounding on
        # hardware that can only handle small ints (like the transfer cards and old android devices)

        return float((self._balance_wei or 0) / int(1e16))

    @balance.setter
    def balance(self, val):
        self._balance_wei = val * int(1e16)

    def decrement_balance(self, val):
        self.increment_balance(-1 * val)

    def increment_balance(self, val):
        # self.balance += val
        val_wei = val * int(1e16)
        if isinstance(val_wei, float):
            val_wei = Decimal(val_wei).quantize(Decimal('1'))

        self._balance_wei = (self._balance_wei or 0) + val_wei

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


    def get_or_create_system_transfer_approval(self):
        sys_blockchain_address = self.organisation.system_blockchain_address

        approval = self.get_approval(sys_blockchain_address)

        if not approval:
            approval = self.give_approval_to_address(sys_blockchain_address)

        return approval

    def give_approval_to_address(self, address_getting_approved):
        approval = SpendApproval(transfer_account_giving_approval=self,
                                 address_getting_approved=address_getting_approved)

        db.session.add(approval)

        return approval

    def get_approval(self, receiving_address):
        for approval in self.spend_approvals_given:
            if approval.receiving_address == receiving_address:
                return approval
        return None

    def approve_and_disburse(self):

        if not self.is_approved:
            self.is_approved = True

            if self.is_beneficiary:
                disbursement = self.make_initial_disbursement()
                return disbursement

    def make_initial_disbursement(self, initial_balance=None):
        from server.utils.credit_transfer import make_payment_transfer
        if not initial_balance:
            initial_balance = current_app.config['STARTING_BALANCE']

        disbursement = make_payment_transfer(initial_balance, token=self.token, send_user=self.primary_user,
                                             receive_user=self.primary_user, transfer_subtype='DISBURSEMENT',
                                             is_ghost_transfer=False, require_sender_approved=False,
                                             require_recipient_approved=False)

        return disbursement

    def initialise_withdrawal(self, withdrawal_amount):
        from server.utils.credit_transfer import make_withdrawal_transfer
        withdrawal = make_withdrawal_transfer(withdrawal_amount,
                                              send_account=self,
                                              automatically_resolve_complete=False)
        return withdrawal

    def _bind_to_organisation(self, organisation):
        if not self.organisation:
            self.organisation = organisation
        if not self.token:
            self.token = organisation.token

    def __init__(self,
                 blockchain_address: Optional[str]=None,
                 bind_to_entity: Optional[Union[Organisation, User]]=None,
                 account_type: Optional[TransferAccountType]=None,
                 private_key: Optional[str] = None,
                 **kwargs):

        super(TransferAccount, self).__init__(**kwargs)

        if bind_to_entity:
            bind_to_entity.transfer_accounts.append(self)

            if isinstance(bind_to_entity, Organisation):
                self.account_type = TransferAccountType.ORGANISATION
                self._bind_to_organisation(bind_to_entity)

            elif isinstance(bind_to_entity, User):
                self.account_type = TransferAccountType.USER
                if bind_to_entity.default_organisation:
                    self._bind_to_organisation(bind_to_entity.default_organisation)

                self.blockchain_address = bind_to_entity.primary_blockchain_address

            elif isinstance(bind_to_entity, ExchangeContract):
                self.account_type = TransferAccountType.CONTRACT
                self.blockchain_address = bind_to_entity.blockchain_address
                self.is_public = True
                self.exchange_contact = self

        if not self.organisation:
            master_organisation = Organisation.master_organisation()
            if not master_organisation:
                raise Exception('master_organisation not found')

            self._bind_to_organisation(master_organisation)

        if blockchain_address:
            self.blockchain_address = blockchain_address


        if not self.blockchain_address:
            self.blockchain_address = bt.create_blockchain_wallet(private_key=private_key)


        if account_type:
            self.account_type = account_type

