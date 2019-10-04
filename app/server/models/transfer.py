import datetime, enum
from sqlalchemy.dialects.postgresql import JSON
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
from server.models.utils import ModelBase, ManyOrgBase, OneOrgBase, user_transfer_account_association_table
from server.models.models import Token
from server.models.user import User
from server.utils.blockchain_tasks import (
    send_eth,
    make_approval
)
from server.exceptions import (
    NoTransferAccountError,
    UserNotFoundError
)
from server.utils.blockchain_tasks import (
    create_blockchain_wallet,
    make_token_transfer,
    get_blockchain_task
)

class TransferTypeEnum(enum.Enum):
    PAYMENT      = "PAYMENT"
    DISBURSEMENT = "DISBURSEMENT"
    WITHDRAWAL   = "WITHDRAWAL"

class TransferModeEnum(enum.Enum):
    NFC = "NFC"
    SMS = "SMS"
    QR  = "QR"
    INTERNAL = "INTERNAL"
    OTHER    = "OTHER"

class TransferStatusEnum(enum.Enum):
    PENDING = 'PENDING'
    REJECTED = 'REJECTED'
    COMPLETE = 'COMPLETE'
    # PENDING = 0
    # INTERNAL_REJECTED = -1
    # INTERNAL_COMPLETE = 1
    # BLOCKCHAIN_REJECTED = -2
    # BLOCKCHAIN_COMPLETE = 2

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
        #TODO(refactor): circular dependency
        from server.utils.credit_transfers import make_disbursement_transfer

        if not initial_balance:
            initial_balance = current_app.config['STARTING_BALANCE']

        disbursement = make_disbursement_transfer(initial_balance, self)

        return disbursement

    def initialise_withdrawal(self, withdrawal_amount):
        #TODO(refactor): circular dependency
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
                                    amount=0.00184196 * 10**18)

        approval_task_id = make_approval(signing_address=transfer_account_giving_approval.blockchain_address,
                                         token=self.token,
                                         spender=address_getting_approved,
                                         amount=1000000,
                                         dependent_on_tasks=[eth_send_task_id])

        self.eth_send_task_id = eth_send_task_id
        self.approval_task_id = approval_task_id

class CreditTransfer(ManyOrgBase, ModelBase):
    __tablename__ = 'credit_transfer'

    uuid            = db.Column(db.String, unique=True)

    resolved_date   = db.Column(db.DateTime)
    transfer_amount = db.Column(db.Integer)

    transfer_type   = db.Column(db.Enum(TransferTypeEnum))
    transfer_status = db.Column(db.Enum(TransferStatusEnum), default=TransferStatusEnum.PENDING)
    transfer_mode   = db.Column(db.Enum(TransferModeEnum))
    transfer_use    = db.Column(JSON)

    resolution_message = db.Column(db.String())

    blockchain_task_id = db.Column(db.Integer)

    token_id        = db.Column(db.Integer, db.ForeignKey(Token.id))

    sender_transfer_account_id       = db.Column(db.Integer, db.ForeignKey(TransferAccount.id))
    recipient_transfer_account_id    = db.Column(db.Integer, db.ForeignKey(TransferAccount.id))

    sender_blockchain_address_id    = db.Column(db.Integer, db.ForeignKey("blockchain_address.id"))
    recipient_blockchain_address_id = db.Column(db.Integer, db.ForeignKey("blockchain_address.id"))

    sender_user_id    = db.Column(db.Integer, db.ForeignKey(User.id))
    recipient_user_id = db.Column(db.Integer, db.ForeignKey(User.id))

    blockchain_transactions = db.relationship('BlockchainTransaction', backref='credit_transfer', lazy=True)

    attached_images = db.relationship('UploadedImage', backref='credit_transfer', lazy=True)

    @hybrid_property
    def blockchain_status(self):
        if self.blockchain_task_id:
            task = get_blockchain_task(self.blockchain_task_id)

            return task.get('status', 'ERROR')
        else:
            return 'UNKNOWN'

        # if len(self.uncompleted_blockchain_tasks) == 0:
        #     return 'COMPLETE'
        #
        # if len(self.pending_blockchain_tasks) > 0:
        #     return 'PENDING'
        #
        # if len(self.failed_blockchain_tasks) > 0:
        #     return 'ERROR'
        #
        # return 'UNKNOWN'


    @hybrid_property
    def blockchain_status_breakdown(self):

        required_task_dict = {x: {'status': 'UNKNOWN', 'hash': None} for x in self._get_required_blockchain_tasks()}

        for transaction in self.blockchain_transactions:
            status_hierarchy = ['UNKNOWN', 'FAILED', 'PENDING', 'SUCCESS']
            task_type = transaction.transaction_type

            current_status = required_task_dict.get(task_type).get('status')
            proposed_new_status = transaction.status

            try:
                if current_status and status_hierarchy.index(proposed_new_status) > status_hierarchy.index(current_status):
                    required_task_dict[task_type]['status'] = proposed_new_status
                    required_task_dict[task_type]['hash'] = transaction.hash
            except ValueError:
                pass

        return required_task_dict

    @hybrid_property
    def pending_blockchain_tasks(self):
        return self._find_blockchain_tasks_with_status_of('PENDING')

    @hybrid_property
    def failed_blockchain_tasks(self):
        return self._find_blockchain_tasks_with_status_of('FAILED')

    @hybrid_property
    def uncompleted_blockchain_tasks(self):
        required_task_set = set(self._get_required_blockchain_tasks())
        completed_task_set = self._find_blockchain_tasks_with_status_of('SUCCESS')
        return required_task_set - completed_task_set

    def _get_required_blockchain_tasks(self):
        if self.transfer_type == TransferTypeEnum.DISBURSEMENT and not current_app.config['IS_USING_BITCOIN']:

            if current_app.config['USING_EXTERNAL_ERC20']:
                master_wallet_approval_status = self.recipient_transfer_account.master_wallet_approval_status

                if (master_wallet_approval_status in ['APPROVED', 'NOT_REQUIRED']
                        and float(current_app.config['FORCE_ETH_DISBURSEMENT_AMOUNT']) <= 0):

                    required_tasks = ['disbursement']

                elif master_wallet_approval_status in ['APPROVED', 'NOT_REQUIRED']:

                    required_tasks = ['disbursement', 'ether load']

                else:
                    required_tasks = ['disbursement', 'ether load', 'master wallet approval']

            else:
                required_tasks = ['initial credit mint']

        else:
            required_tasks = ['transfer']

        return required_tasks

    def _find_blockchain_tasks_with_status_of(self, required_status):
        if required_status not in ['PENDING', 'SUCCESS', 'FAILED']:
            raise Exception('required_status must be one of PENDING, SUCCESS or FAILED')

        completed_task_set = set()
        for transaction in self.blockchain_transactions:
            if transaction.status == required_status:
                completed_task_set.add(transaction.transaction_type)
        return completed_task_set

    def send_blockchain_payload_to_worker(self, is_retry=False):

        sender_approval = self.sender_transfer_account.get_or_create_system_transfer_approval()

        recipient_approval = self.recipient_transfer_account.get_or_create_system_transfer_approval()

        self.blockchain_task_id = make_token_transfer(
            signing_address=self.sender_transfer_account.organisation.system_blockchain_address,
            token=self.token,
            from_address=self.sender_transfer_account.blockchain_address,
            to_address=self.recipient_transfer_account.blockchain_address,
            amount=self.transfer_amount,
            dependent_on_tasks=[
                sender_approval.eth_send_task_id, sender_approval.approval_task_id,
                recipient_approval.eth_send_task_id, recipient_approval.approval_task_id
            ]
        )

    def resolve_as_completed(self, existing_blockchain_txn=None):
        self.resolved_date = datetime.datetime.utcnow()
        self.transfer_status = TransferStatusEnum.COMPLETE

        self.sender_transfer_account.balance -= self.transfer_amount
        self.recipient_transfer_account.balance += self.transfer_amount

        if self.transfer_type == TransferTypeEnum.DISBURSEMENT:
            if self.recipient_user and self.recipient_user.transfer_card:
                self.recipient_user.transfer_card.update_transfer_card()

        if not existing_blockchain_txn:
            self.send_blockchain_payload_to_worker()

    def resolve_as_rejected(self, message=None):
        self.resolved_date = datetime.datetime.utcnow()
        self.transfer_status = TransferStatusEnum.REJECTED

        if message:
            self.resolution_message = message

    def check_sender_has_sufficient_balance(self):
        return self.sender_user and self.sender_transfer_account.balance - self.transfer_amount >= 0

    def check_sender_is_approved(self):
        return self.sender_user and self.sender_transfer_account.is_approved

    def check_recipient_is_approved(self):
        return self.recipient_user and self.recipient_transfer_account.is_approved

    def find_user_transfer_accounts_with_matching_token(self, user, token):
        matching_transfer_accounts = []
        for transfer_account in user.transfer_accounts:
            if transfer_account.token == token:
                matching_transfer_accounts.append(transfer_account)
        if len(matching_transfer_accounts) == 0:
            raise NoTransferAccountError("No transfer account for user {} and token".format(user, token))
        if len(matching_transfer_accounts) > 1:
            raise Exception(f"User has multiple transfer accounts for token {token}")

        return matching_transfer_accounts[0]

    def _select_transfer_account(self, supplied_transfer_account, user, token):
        if token is None:
            raise Exception("Token must be specified")
        if supplied_transfer_account:
            if user is not None and user not in supplied_transfer_account.users:
                raise UserNotFoundError(f'User {user} not found for transfer account {supplied_transfer_account}')
            return supplied_transfer_account

        return self.find_user_transfer_accounts_with_matching_token(user, token)

    def append_organisation_if_required(self, organisation):
        if organisation not in self.organisations:
            self.organisations.append(organisation)

    def __init__(self,
                 amount,
                 token=None,
                 sender_user=None,
                 recipient_user=None,
                 sender_transfer_account=None,
                 recipient_transfer_account=None,
                 transfer_type=None, uuid=None):

        self.transfer_amount = amount

        self.sender_user = sender_user
        self.recipient_user = recipient_user

        self.sender_transfer_account = sender_transfer_account or self._select_transfer_account(
            sender_transfer_account, sender_user, token)

        self.token = token or self.sender_transfer_account.token

        self.recipient_transfer_account = recipient_transfer_account or self._select_transfer_account(
            recipient_transfer_account, recipient_user, self.token)

        if self.sender_transfer_account.token != self.recipient_transfer_account.token:
            raise Exception("Tokens do not match")

        self.transfer_type = transfer_type

        if uuid is not None:
            self.uuid = uuid

        self.append_organisation_if_required(self.recipient_transfer_account.organisation)
        self.append_organisation_if_required(self.sender_transfer_account.organisation)

class BlockchainTransaction(ModelBase):
    __tablename__ = 'blockchain_transaction'

    status = db.Column(db.String)  # PENDING, SUCCESS, FAILED
    message = db.Column(db.String)
    block = db.Column(db.Integer)
    submitted_date = db.Column(db.DateTime)
    added_date = db.Column(db.DateTime)
    hash = db.Column(db.String)
    nonce = db.Column(db.Integer)
    transaction_type = db.Column(db.String)

    is_bitcoin = db.Column(db.Boolean)

    # Output spent txn for bitcoin
    has_output_txn = db.Column(db.Boolean, default=False)

    credit_transfer_id = db.Column(db.Integer, db.ForeignKey(CreditTransfer.id))

    signing_blockchain_address_id = db.Column(db.Integer, db.ForeignKey('blockchain_address.id'))

class TransferCard(ModelBase):
    __tablename__ = 'transfer_card'

    public_serial_number = db.Column(db.String)
    nfc_serial_number    = db.Column(db.String)
    PIN                  = db.Column(db.String)

    _amount_loaded          = db.Column(db.Integer)
    amount_loaded_signature = db.Column(db.String)

    user_id    = db.Column(db.Integer, db.ForeignKey(User.id))

    transfer_account_id    = db.Column(db.Integer, db.ForeignKey(TransferAccount.id))


    @hybrid_property
    def amount_loaded(self):
        return self._phone

    @amount_loaded.setter
    def amount_loaded(self, amount):
        self._amount_loaded = amount
        message = '{}{}{}'.format(self.nfc_serial_number, amount, self.transfer_account.token.symbol)
        self.amount_loaded_signature = current_app.config['ECDSA_SIGNING_KEY'].sign(message.encode()).hex()

    def update_transfer_card(self):
        disbursements = (CreditTransfer.query
                         .execution_options(show_all=True)
                         .filter_by(recipient_user_id=self.user_id)
                         .filter_by(transfer_type=TransferTypeEnum.DISBURSEMENT)
                         .filter_by(transfer_status=TransferStatusEnum.COMPLETE)
                         .all())

        total_disbursed = 0

        for disbursement in disbursements:
            total_disbursed += disbursement.transfer_amount

        self.amount_loaded = total_disbursed

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
