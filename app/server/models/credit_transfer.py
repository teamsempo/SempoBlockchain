import datetime
from typing import List
from decimal import Decimal

from sqlalchemy.dialects.postgresql import JSON, JSONB
from flask import current_app, g
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Index
from sqlalchemy.sql import func
from sqlalchemy import or_
from uuid import uuid4

from server import db, bt
from server.models.utils import BlockchainTaskableBase, ManyOrgBase, credit_transfer_transfer_usage_association_table,\
    disbursement_credit_transfer_association_table, credit_transfer_approver_user_association_table
from server.models.token import Token
from server.models.transfer_account import TransferAccount
from server.utils.access_control import AccessControl
from server.utils.metrics.metrics_cache import clear_metrics_cache

from server.exceptions import (
    TransferLimitError,
    InsufficientBalanceError,
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
    batch_uuid      = db.Column(db.String)

    # override ModelBase deleted to add an index
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

    resolved_date   = db.Column(db.DateTime)
    _transfer_amount_wei = db.Column(db.Numeric(27), default=0)

    transfer_type       = db.Column(db.Enum(TransferTypeEnum), index=True)
    transfer_subtype    = db.Column(db.Enum(TransferSubTypeEnum))
    transfer_status     = db.Column(db.Enum(TransferStatusEnum), default=TransferStatusEnum.PENDING)
    transfer_mode       = db.Column(db.Enum(TransferModeEnum), index=True)
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

    sender_transfer_account_id       = db.Column(db.Integer, db.ForeignKey("transfer_account.id"), index=True)
    sender_transfer_account          = db.relationship('TransferAccount', foreign_keys=[sender_transfer_account_id], back_populates='credit_sends', lazy='joined')

    recipient_transfer_account_id    = db.Column(db.Integer, db.ForeignKey("transfer_account.id"), index=True)
    recipient_transfer_account          = db.relationship('TransferAccount', foreign_keys=[recipient_transfer_account_id], back_populates='credit_receives', lazy='joined')

    received_third_party_sync = db.Column(db.Boolean, default=False)
    
    sender_blockchain_address_id    = db.Column(db.Integer, db.ForeignKey("blockchain_address.id"), index=True)
    recipient_blockchain_address_id = db.Column(db.Integer, db.ForeignKey("blockchain_address.id"), index=True)

    sender_transfer_card_id = db.Column(db.Integer, db.ForeignKey("transfer_card.id"), index=True)

    sender_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)

    is_initial_disbursement = db.Column(db.Boolean, default=False)

    attached_images = db.relationship('UploadedResource', backref='credit_transfer', lazy='joined')

    fiat_ramp = db.relationship('FiatRamp', backref='credit_transfer', lazy=True, uselist=False)

    __table_args__ = (Index('updated_index', "updated"), )

    from_exchange = db.relationship('Exchange', backref='from_transfer', lazy='joined', uselist=False,
                                     foreign_keys='Exchange.from_transfer_id')

    to_exchange = db.relationship('Exchange', backref='to_transfer', lazy=True, uselist=False,
                                  foreign_keys='Exchange.to_transfer_id')

    disbursement = db.relationship(
        "Disbursement",
        secondary=disbursement_credit_transfer_association_table,
        back_populates="credit_transfers",
        uselist=False
    )

    approvers = db.relationship(
        "User",
        secondary=credit_transfer_approver_user_association_table,
        lazy=True
    )

    def add_message(self, message):
        dated_message = f"[{datetime.datetime.utcnow()}:: {message}]"
        self.resolution_message = dated_message

    # TODO: Apply this to all transfer amounts/balances, work out the correct denominator size
    @hybrid_property
    def transfer_amount(self):
        return (self._transfer_amount_wei or 0) / int(1e16)

    @transfer_amount.setter
    def transfer_amount(self, val):
        self._transfer_amount_wei = val * int(1e16)

    @hybrid_property
    def rounded_transfer_amount(self):
        return (self._transfer_amount_wei or 0) / int(1e18)

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

        # Approval is called so that the master account can make transactions on behalf of the transfer account.
        # Make sure this approval is done first before making a transaction
        approval_priors = list(
            filter(lambda x: x is not None,
                   [
                       sender_approval.eth_send_task_uuid, sender_approval.approval_task_uuid,
                       recipient_approval.eth_send_task_uuid, recipient_approval.approval_task_uuid
                   ]))

        # Forces an order on transactions so that if there's an outage somewhere, transactions don't get confirmed
        # On chain in an order that leads to a unrecoverable state
        other_priors = [t.blockchain_task_uuid for t in self._get_required_prior_tasks()]

        all_priors = approval_priors + other_priors

        return bt.make_token_transfer(
            signing_address=self.sender_transfer_account.organisation.system_blockchain_address,
            token=self.token,
            from_address=self.sender_transfer_account.blockchain_address,
            to_address=self.recipient_transfer_account.blockchain_address,
            amount=self.transfer_amount,
            prior_tasks=all_priors,
            queue=queue,
            task_uuid=self.blockchain_task_uuid
        )

    def _get_required_prior_tasks(self):
        """
        Get the tasks involving the sender's account that must complete prior to this task being submitted to chain
        To calculate the prior tasks for the sender Alice:

        - Find the most recent credit transfer where Alice was the sender, not including any transfers that have the
            same batch UUID as this transfer. Call this "most_recent_out_of_batch_send"
        - Find all credit transfers subsequent to "most_recent_out_of_batch_send" where Alice was the recipient. Call
            this "more_recent_receives"

        Required priors are all transfers in "more_recent_receives" and "most_recent_out_of_batch_send".
        For why this works, see https://github.com/teamsempo/SempoBlockchain/pull/262

        """
        # We're constantly querying complete transfers here. Lazy and DRY
        complete_transfer_base_query = (
            CreditTransfer.query.filter(CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE)
        ).execution_options(show_all=True)

        # Query for finding the most recent transfer sent by the sending account that isn't from the same batch uuid
        # that of the transfer in question
        most_recent_out_of_batch_send = (
            complete_transfer_base_query
                .order_by(CreditTransfer.id.desc())
                .filter(CreditTransfer.sender_transfer_account == self.sender_transfer_account)
                .filter(CreditTransfer.id != self.id)
                .filter(or_(CreditTransfer.batch_uuid != self.batch_uuid,
                            CreditTransfer.batch_uuid == None  # Only exclude matching batch_uuids if they're not null
                            )
                ).execution_options(show_all=True).first()
        )

        # Base query for finding more_recent_receives
        base_receives_query = (
            complete_transfer_base_query
                .filter(CreditTransfer.recipient_transfer_account == self.sender_transfer_account)
        ).execution_options(show_all=True)

        if most_recent_out_of_batch_send:
            # If most_recent_out_of_batch_send exists, find all receive transfers since it.
            more_recent_receives = base_receives_query.filter(CreditTransfer.id > most_recent_out_of_batch_send.id).all()

            # Required priors are then the out of batch send plus these receive transfers
            required_priors = more_recent_receives + [most_recent_out_of_batch_send]

            # Edge case handle: if most_recent_out_of_batch_send is a batch member, the whole batch are priors as well
            if most_recent_out_of_batch_send.batch_uuid is not None:
                same_batch_priors = complete_transfer_base_query.filter(
                    CreditTransfer.batch_uuid == most_recent_out_of_batch_send.batch_uuid
                ).execution_options(show_all=True).all()

                required_priors = required_priors + same_batch_priors

        else:
            # Otherwise, return all receives, which are all our required priors
            required_priors = base_receives_query.all()

        # Filter out any transfers that we already know are complete - there's no reason to create an extra dep
        # We don't do this inside the Alchemy queries because we need the completed priors to calculate other priors
        required_priors = [prior for prior in required_priors if prior.blockchain_status != BlockchainStatus.SUCCESS]

        # Remove any possible duplicates
        return set(required_priors)

    def add_approver_and_resolve_as_completed(self, user=None):
        # Adds approver to transfer, resolves as complete if it can!
        if not user:
            user = g.user
        if user not in self.approvers:
            self.approvers.append(user)
        if len(self.approvers) == 1:
            if current_app.config['REQUIRE_MULTIPLE_APPROVALS']:
                self.transfer_status = TransferStatusEnum.PARTIAL
        if self.check_if_fully_approved():
            self.resolve_as_complete_and_trigger_blockchain()

    def check_if_fully_approved(self):
        # Checks if the credit transfer is approved and ready to be resolved as complete
        if current_app.config['REQUIRE_MULTIPLE_APPROVALS'] and not AccessControl.has_sufficient_tier(g.user.roles, 'ADMIN', 'sempoadmin'):
            if len(self.approvers) <=1:
                return False
            else:
                return True
        else:
            return True

    def resolve_as_complete_with_existing_blockchain_transaction(self, transaction_hash):

        self.resolve_as_complete()

        self.blockchain_status = BlockchainStatus.SUCCESS
        self.blockchain_hash = transaction_hash

    def resolve_as_complete_and_trigger_blockchain(
            self,
            existing_blockchain_txn=None,
            queue='high-priority',
            batch_uuid: str=None
    ):

        self.resolve_as_complete(batch_uuid)

        if not existing_blockchain_txn:
            self.blockchain_task_uuid = str(uuid4())
            g.pending_transactions.append((self, queue))

    def resolve_as_complete(self, batch_uuid=None):
        if self.transfer_status not in [None, TransferStatusEnum.PENDING, TransferStatusEnum.PARTIAL]:
            raise Exception(f'Resolve called multiple times for transfer {self.id}')
        try:
            self.check_sender_transfer_limits()
        except TransferLimitError as e:
            # Sempo admins can always bypass limits, allowing for things like emergency moving of funds etc
            if hasattr(g, 'user') and AccessControl.has_suffient_role(g.user.roles, {'ADMIN': 'sempoadmin'}):
                self.add_message(f'Warning: {e}')
            else:
                raise e

        self.resolved_date = datetime.datetime.utcnow()
        self.transfer_status = TransferStatusEnum.COMPLETE
        self.update_balances()

        if (datetime.datetime.utcnow() - self.created).seconds > 5:
            clear_metrics_cache()

        if self.transfer_type == TransferTypeEnum.PAYMENT and self.transfer_subtype == TransferSubTypeEnum.DISBURSEMENT:
            if self.recipient_user and self.recipient_user.transfer_card:
                self.recipient_user.transfer_card.update_transfer_card()

        if batch_uuid:
            self.batch_uuid = batch_uuid

        if self.fiat_ramp and self.transfer_type in [TransferTypeEnum.DEPOSIT, TransferTypeEnum.WITHDRAWAL]:
            self.fiat_ramp.resolve_as_complete()

    def resolve_as_rejected(self, message=None):
        if self.transfer_status not in [None, TransferStatusEnum.PENDING]:
            raise Exception(f'Resolve called multiple times for transfer {self.id}')

        if self.fiat_ramp and self.transfer_type in [TransferTypeEnum.DEPOSIT, TransferTypeEnum.WITHDRAWAL]:
            self.fiat_ramp.resolve_as_rejected()

        self.resolved_date = datetime.datetime.utcnow()
        self.transfer_status = TransferStatusEnum.REJECTED
        self.blockchain_status = BlockchainStatus.UNSTARTED
        self.update_balances()

        if message:
            self.add_message(message)

    def update_balances(self):
        self.sender_transfer_account.update_balance()
        self.recipient_transfer_account.update_balance()


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
        return self.sender_transfer_account.unrounded_balance - Decimal(self.transfer_amount) >= 0

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
                 transfer_card=None,
                 is_ghost_transfer=False,
                 require_sufficient_balance=True
                 ):

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

        if transfer_type is TransferTypeEnum.DEPOSIT:
            self.sender_transfer_account = self.recipient_transfer_account.token.float_account

        if transfer_type is TransferTypeEnum.WITHDRAWAL:
            self.recipient_transfer_account = self.sender_transfer_account.token.float_account

        try:
            self.recipient_transfer_account = recipient_transfer_account or self.recipient_transfer_account or self._select_transfer_account(
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

        if self.sender_transfer_account.token != self.recipient_transfer_account.token:
            raise Exception("Tokens do not match")

        self.transfer_type = transfer_type
        self.transfer_subtype = transfer_subtype
        self.transfer_mode = transfer_mode
        self.transfer_metadata = transfer_metadata
        self.transfer_card = transfer_card

        if uuid is not None:
            self.uuid = uuid

        self.append_organisation_if_required(self.recipient_transfer_account.organisation)
        self.append_organisation_if_required(self.sender_transfer_account.organisation)

        if require_sufficient_balance and not self.check_sender_has_sufficient_balance():
            message = "Sender {} has insufficient balance. Has {}, needs {}.".format(
                self.sender_transfer_account,
                self.sender_transfer_account.balance,
                self.transfer_amount
            )
            self.resolve_as_rejected(message)
            raise InsufficientBalanceError(message)

        self.update_balances()
