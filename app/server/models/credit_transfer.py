import datetime
from typing import List

from sqlalchemy.dialects.postgresql import JSON, JSONB
from flask import current_app, g
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Index
from sqlalchemy.sql import func
from uuid import uuid4

from server import db, bt
from server.models.utils import BlockchainTaskableBase, ManyOrgBase, credit_transfer_transfer_usage_association_table
from server.models.token import Token
from server.models.transfer_account import TransferAccount

from server.exceptions import (
    NoTransferAccountError,
    MinimumSentLimitError,
    NoTransferAllowedLimitError,
    MaximumPerTransferLimitError,
    TransferAmountLimitError,
    TransferCountLimitError,
    TransferBalanceFractionLimitError)

from server.utils.transfer_account import find_transfer_accounts_with_matching_token

from server.utils.transfer_enums import (
    TransferTypeEnum,
    TransferSubTypeEnum,
    TransferStatusEnum,
    TransferModeEnum,
    BlockchainStatus
)


class CreditTransfer(ManyOrgBase, BlockchainTaskableBase):
    __tablename__ = 'credit_transfer'

    uuid            = db.Column(db.String, unique=True)

    resolved_date   = db.Column(db.DateTime)
    _transfer_amount_wei = db.Column(db.Numeric(27), default=0)

    transfer_type       = db.Column(db.Enum(TransferTypeEnum), index=True)
    transfer_subtype    = db.Column(db.Enum(TransferSubTypeEnum))
    transfer_status     = db.Column(db.Enum(TransferStatusEnum), default=TransferStatusEnum.PENDING)
    transfer_mode       = db.Column(db.Enum(TransferModeEnum))
    transfer_use        = db.Column(JSON) # Deprecated
    transfer_usages = db.relationship(
        "TransferUsage",
        secondary=credit_transfer_transfer_usage_association_table,
        back_populates="credit_transfers",
        lazy='joined'
    )
    transfer_metadata = db.Column(JSONB)

    exclude_from_limit_calcs = db.Column(db.Boolean, default=False)

    resolution_message = db.Column(db.String())

    token_id        = db.Column(db.Integer, db.ForeignKey(Token.id))

    sender_transfer_account_id       = db.Column(db.Integer, db.ForeignKey("transfer_account.id"))
    sender_transfer_account          = db.relationship('TransferAccount', foreign_keys=[sender_transfer_account_id], back_populates='credit_sends', lazy='joined')

    recipient_transfer_account_id    = db.Column(db.Integer, db.ForeignKey("transfer_account.id"))
    recipient_transfer_account          = db.relationship('TransferAccount', foreign_keys=[recipient_transfer_account_id], back_populates='credit_receives', lazy='joined')

    received_third_party_sync = db.Column(db.Boolean, default=False)

    sender_blockchain_address_id    = db.Column(db.Integer, db.ForeignKey("blockchain_address.id"))
    recipient_blockchain_address_id = db.Column(db.Integer, db.ForeignKey("blockchain_address.id"))

    sender_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    attached_images = db.relationship('UploadedResource', backref='credit_transfer', lazy='joined')

    fiat_ramp = db.relationship('FiatRamp', backref='credit_transfer', lazy=True, uselist=False)

    __table_args__ = (Index('updated_index', "updated"), )

    from_exchange = db.relationship('Exchange', backref='from_transfer', lazy='joined', uselist=False,
                                     foreign_keys='Exchange.from_transfer_id')

    to_exchange = db.relationship('Exchange', backref='to_transfer', lazy=True, uselist=False,
                                  foreign_keys='Exchange.to_transfer_id')

    # TODO: Apply this to all transfer amounts/balances, work out the correct denominator size
    @hybrid_property
    def transfer_amount(self):
        return (self._transfer_amount_wei or 0) / int(1e16)

    @transfer_amount.setter
    def transfer_amount(self, val):
        self._transfer_amount_wei = val * int(1e16)

    @hybrid_property
    def public_transfer_type(self):
        if self.transfer_type == TransferTypeEnum.PAYMENT:
            if self.transfer_subtype == TransferSubTypeEnum.STANDARD or None:
                return TransferTypeEnum.PAYMENT
            else:
                return self.transfer_subtype
        else:
            return self.transfer_type

    @public_transfer_type.expression
    def public_transfer_type(cls):
        from sqlalchemy import case, cast, String
        return case([
                (cls.transfer_subtype == TransferSubTypeEnum.STANDARD, cast(cls.transfer_type, String)),
                (cls.transfer_type == TransferTypeEnum.PAYMENT, cast(cls.transfer_subtype, String)),
            ],
            else_ = cast(cls.transfer_type, String)
        )

    def send_blockchain_payload_to_worker(self, is_retry=False, queue='high-priority'):
        sender_approval = self.sender_transfer_account.get_or_create_system_transfer_approval()
        recipient_approval = self.recipient_transfer_account.get_or_create_system_transfer_approval()
        return bt.make_token_transfer(
            signing_address=self.sender_transfer_account.organisation.system_blockchain_address,
            token=self.token,
            from_address=self.sender_transfer_account.blockchain_address,
            to_address=self.recipient_transfer_account.blockchain_address,
            amount=self.transfer_amount,
            prior_tasks=
            list(filter(lambda x: x is not None,
                        [
                            sender_approval.eth_send_task_uuid, sender_approval.approval_task_uuid,
                            recipient_approval.eth_send_task_uuid, recipient_approval.approval_task_uuid
                        ])),
            queue=queue,
            task_uuid=self.blockchain_task_uuid
        )

    def resolve_as_complete_with_existing_blockchain_transaction(self, transaction_hash):

        self.resolve_as_complete()

        self.blockchain_status = BlockchainStatus.SUCCESS
        self.blockchain_hash = transaction_hash

    def resolve_as_complete_and_trigger_blockchain(self, existing_blockchain_txn=None, queue='high-priority'):

        self.resolve_as_complete()

        if not existing_blockchain_txn:
            self.blockchain_task_uuid = str(uuid4())
            g.pending_transactions.append((self, queue))

    def resolve_as_complete(self):
        if self.transfer_status not in [None, TransferStatusEnum.PENDING]:
            raise Exception(f'Transfer resolve function called multiple times for transaction {self.id}')
        self.check_sender_transfer_limits()
        self.resolved_date = datetime.datetime.utcnow()
        self.transfer_status = TransferStatusEnum.COMPLETE
        self.sender_transfer_account.update_balance()
        self.recipient_transfer_account.update_balance()

        if self.transfer_type == TransferTypeEnum.PAYMENT and self.transfer_subtype == TransferSubTypeEnum.DISBURSEMENT:
            if self.recipient_user and self.recipient_user.transfer_card:
                self.recipient_user.transfer_card.update_transfer_card()

        if self.fiat_ramp and self.transfer_type in [TransferTypeEnum.DEPOSIT, TransferTypeEnum.WITHDRAWAL]:
            self.fiat_ramp.resolve_as_complete()

    def resolve_as_rejected(self, message=None):
        if self.transfer_status not in [None, TransferStatusEnum.PENDING]:
            raise Exception(f'Transfer resolve function called multiple times for transaciton {self.id}')

        if self.fiat_ramp and self.transfer_type in [TransferTypeEnum.DEPOSIT, TransferTypeEnum.WITHDRAWAL]:
            self.fiat_ramp.resolve_as_rejected()

        self.resolved_date = datetime.datetime.utcnow()
        self.transfer_status = TransferStatusEnum.REJECTED

        if message:
            self.resolution_message = message

    def get_transfer_limits(self):
        from server.utils.transfer_limits import (LIMIT_IMPLEMENTATIONS, get_applicable_transfer_limits)

        return get_applicable_transfer_limits(LIMIT_IMPLEMENTATIONS, self)

    def check_sender_transfer_limits(self):
        if self.sender_user is None:
            # skip if there is no sender, which implies system send
            return

        relevant_transfer_limits = self.get_transfer_limits()

        for limit in relevant_transfer_limits:

            try:
                limit.validate_transfer(self)
            except (
                    TransferAmountLimitError,
                    TransferCountLimitError,
                    TransferBalanceFractionLimitError,
                    MaximumPerTransferLimitError,
                    MinimumSentLimitError,
                    NoTransferAllowedLimitError
            ) as e:
                self.resolve_as_rejected(message=e.message)
                raise e

        return relevant_transfer_limits

    def check_sender_has_sufficient_balance(self):
        return self.sender_user and self.sender_transfer_account.balance - self.transfer_amount >= 0

    def check_sender_is_approved(self):
        return self.sender_user and self.sender_transfer_account.is_approved

    def check_recipient_is_approved(self):
        return self.recipient_user and self.recipient_transfer_account.is_approved

    def _select_transfer_account(self, token, user):
        if token is None:
            raise Exception("Token must be specified")
        return find_transfer_accounts_with_matching_token(user, token)

    def append_organisation_if_required(self, organisation):
        if organisation and organisation not in self.organisations:
            self.organisations.append(organisation)

    def __init__(self,
                 amount,
                 token=None,
                 sender_user=None,
                 recipient_user=None,
                 sender_transfer_account=None,
                 recipient_transfer_account=None,
                 transfer_type: TransferTypeEnum=None,
                 uuid=None,
                 transfer_metadata=None,
                 fiat_ramp=None,
                 transfer_subtype: TransferSubTypeEnum=None,
                 transfer_mode: TransferModeEnum = None,
                 is_ghost_transfer=False):

        if amount < 0:
            raise Exception("Negative amount provided")
        self.transfer_amount = amount

        self.sender_user = sender_user
        self.recipient_user = recipient_user

        self.sender_transfer_account = sender_transfer_account or self._select_transfer_account(
            token,
            sender_user
        )

        self.token = token or self.sender_transfer_account.token

        self.fiat_ramp = fiat_ramp

        try:
            self.recipient_transfer_account = recipient_transfer_account or self._select_transfer_account(
                self.token,
                recipient_user
            )

            if is_ghost_transfer is False:
                self.recipient_transfer_account.is_ghost = False
        except NoTransferAccountError:
            self.recipient_transfer_account = TransferAccount(
                bound_entity=recipient_user,
                token=token,
                is_approved=True,
                is_ghost=is_ghost_transfer
            )
            db.session.add(self.recipient_transfer_account)

        if transfer_type is TransferTypeEnum.DEPOSIT:
            self.sender_transfer_account = self.recipient_transfer_account.get_float_transfer_account()

        if transfer_type is TransferTypeEnum.WITHDRAWAL:
            self.recipient_transfer_account = self.sender_transfer_account.get_float_transfer_account()

        if self.sender_transfer_account.token != self.recipient_transfer_account.token:
            raise Exception("Tokens do not match")

        self.transfer_type = transfer_type
        self.transfer_subtype = transfer_subtype
        self.transfer_mode = transfer_mode
        self.transfer_metadata = transfer_metadata

        if uuid is not None:
            self.uuid = uuid

        self.append_organisation_if_required(self.recipient_transfer_account.organisation)
        self.append_organisation_if_required(self.sender_transfer_account.organisation)
