import datetime
from sqlalchemy.sql import func
import os, base64
from eth_utils import keccak
from flask import current_app
from cryptography.fernet import Fernet
from sqlalchemy.ext.hybrid import hybrid_property
from web3 import Web3

from server.utils.misc import hex_private_key_to_address
from server.constants import (
    ALLOWED_BLOCKCHAIN_ADDRESS_TYPES
)
from server import db
from server.models.utils import ModelBase, OneOrgBase, user_transfer_account_association_table
from server.models.models import Token
from server.models.user import User
from server.models.credit_transfer import CreditTransfer, BlockchainTransaction
from server.utils.blockchain_tasks import (
    send_eth,
    make_approval
)
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

    token_id        = db.Column(db.Integer, db.ForeignKey(Token.id))

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
            db.session.query(func.sum(CreditTransfer.transfer_amount).label('total')).execution_options(show_all=True)
            .filter(CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE)
            .filter(CreditTransfer.sender_transfer_account_id == self.id).first().total or 0
        )

    @hybrid_property
    def total_received(self):
        return int(
            db.session.query(func.sum(CreditTransfer.transfer_amount).label('total')).execution_options(show_all=True)
            .filter(CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE)
            .filter(CreditTransfer.recipient_transfer_account_id == self.id).first().total or 0
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

    def __init__(self, blockchain_address=None, organisation=None):
        #
        # blockchain_address_obj = BlockchainAddress(type="TRANSFER_ACCOUNT", blockchain_address=blockchain_address)
        # db.session.add(blockchain_address_obj)

        self.blockchain_address = blockchain_address or create_blockchain_wallet()

        if organisation:
            self.organisation = organisation
            self.token = organisation.token

class SpendApproval(ModelBase):
    __tablename__ = 'spend_approval'

    eth_send_task_id = db.Column(db.Integer)
    approval_task_id = db.Column(db.Integer)
    receiving_address = db.Column(db.String)

    token_id                      = db.Column(db.Integer, db.ForeignKey(Token.id))
    giving_transfer_account_id    = db.Column(db.Integer, db.ForeignKey(TransferAccount.id))

    def __init__(self, transfer_account_giving_approval, address_getting_approved):

        self.giving_transfer_account = transfer_account_giving_approval

        self.token = transfer_account_giving_approval.token

        self.receiving_address = address_getting_approved

        eth_send_task_id = send_eth(signing_address=address_getting_approved,
                                    recipient_address=transfer_account_giving_approval.blockchain_address,
                                    amount_wei=0.00184196 * 10**18)

        approval_task_id = make_approval(signing_address=transfer_account_giving_approval.blockchain_address,
                                         token=self.token,
                                         spender=address_getting_approved,
                                         amount=1000000,
                                         dependent_on_tasks=[eth_send_task_id])

        self.eth_send_task_id = eth_send_task_id
        self.approval_task_id = approval_task_id

class BlockchainAddress(OneOrgBase, ModelBase):
    __tablename__ = 'blockchain_address'

    address             = db.Column(db.String())
    encoded_private_key = db.Column(db.String())

    # Either "MASTER", "TRANSFER_ACCOUNT" or "EXTERNAL"
    type = db.Column(db.String())

    transfer_account_id = db.Column(db.Integer, db.ForeignKey(TransferAccount.id))

    signed_transactions = db.relationship('BlockchainTransaction',
                                          backref='signing_blockchain_address',
                                          lazy='dynamic',
                                          foreign_keys='BlockchainTransaction.signing_blockchain_address_id')

    credit_sends = db.relationship('CreditTransfer', backref='sender_blockchain_address',
                                   lazy='dynamic', foreign_keys='CreditTransfer.sender_blockchain_address_id')

    credit_receives = db.relationship('CreditTransfer', backref='recipient_blockchain_address',
                                      lazy='dynamic', foreign_keys='CreditTransfer.recipient_blockchain_address_id')

    @hybrid_property
    def decrypted_private_key(self):

        fernet_encryption_key = base64.b64encode(keccak(text=current_app.config['SECRET_KEY']))
        cipher_suite = Fernet(fernet_encryption_key)

        return cipher_suite.decrypt(self.encoded_private_key.encode('utf-8')).decode('utf-8')

    def encrypt_private_key(self, unencoded_private_key):

        fernet_encryption_key = base64.b64encode(keccak(text=current_app.config['SECRET_KEY']))
        cipher_suite = Fernet(fernet_encryption_key)

        return cipher_suite.encrypt(unencoded_private_key.encode('utf-8')).decode('utf-8')

    def calculate_address(self, private_key):
        self.address = hex_private_key_to_address(private_key)

    def allowed_types(self):
        return ALLOWED_BLOCKCHAIN_ADDRESS_TYPES

    def __init__(self, type, blockchain_address=None):

        if type not in self.allowed_types():
            raise Exception("type {} not one of {}".format(type, self.allowed_types()))

        self.type = type

        if blockchain_address:
            self.address = blockchain_address

        if self.type == "TRANSFER_ACCOUNT" and not blockchain_address:

            hex_private_key = Web3.toHex(keccak(os.urandom(4096)))

            self.encoded_private_key = self.encrypt_private_key(hex_private_key)

            self.calculate_address(hex_private_key)
