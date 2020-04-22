import datetime
from typing import List

from sqlalchemy.dialects.postgresql import JSON, JSONB
from flask import current_app
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Index
from sqlalchemy.sql import func

from server import db, bt
from server.models.utils import BlockchainTaskableBase, ManyOrgBase
from server.models.token import Token
from server.models.transfer_account import TransferAccount

from server.exceptions import (
    NoTransferAccountError,
    UserNotFoundError,
    NoTransferAllowedLimitError,
    TransferAmountLimitError,
    TransferCountLimitError,
    TransferBalanceFractionLimitError)

from server.utils.transfer_account import find_transfer_accounts_with_matching_token

from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum, TransferStatusEnum, TransferModeEnum


class CreditTransfer(ManyOrgBase, BlockchainTaskableBase):
    __tablename__ = 'credit_transfer'

    uuid            = db.Column(db.String, unique=True)

    resolved_date   = db.Column(db.DateTime)
    _transfer_amount_wei = db.Column(db.Numeric(27), default=0)

    transfer_type       = db.Column(db.Enum(TransferTypeEnum), index=True)
    transfer_subtype    = db.Column(db.Enum(TransferSubTypeEnum))
    transfer_status     = db.Column(db.Enum(TransferStatusEnum), default=TransferStatusEnum.PENDING)
    transfer_mode       = db.Column(db.Enum(TransferModeEnum))
    transfer_use        = db.Column(JSON)

    transfer_metadata = db.Column(JSONB)

    exclude_from_limit_calcs = db.Column(db.Boolean, default=False)

    resolution_message = db.Column(db.String())

    token_id        = db.Column(db.Integer, db.ForeignKey(Token.id))

    sender_transfer_account_id       = db.Column(db.Integer, db.ForeignKey("transfer_account.id"))
    recipient_transfer_account_id    = db.Column(db.Integer, db.ForeignKey("transfer_account.id"))

    sender_blockchain_address_id    = db.Column(db.Integer, db.ForeignKey("blockchain_address.id"))
    recipient_blockchain_address_id = db.Column(db.Integer, db.ForeignKey("blockchain_address.id"))

    sender_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    blockchain_transactions = db.relationship('BlockchainTransaction', backref='credit_transfer', lazy=True)

    attached_images = db.relationship('UploadedResource', backref='credit_transfer', lazy=True)

    fiat_ramp = db.relationship('FiatRamp', backref='credit_transfer', lazy=True, uselist=False)

    __table_args__ = (Index('updated_index', "updated"), )

    from_exchange = db.relationship('Exchange', backref='from_transfer', lazy=True, uselist=False,
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

    def send_blockchain_payload_to_worker(self, is_retry=False, queue='high-priority'):
        sender_approval = self.sender_transfer_account.get_or_create_system_transfer_approval()

        recipient_approval = self.recipient_transfer_account.get_or_create_system_transfer_approval()
        self.blockchain_task_uuid = bt.make_token_transfer(
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
            queue=queue
        )

    def resolve_as_completed(self, existing_blockchain_txn=None, queue='high-priority'):
        self.check_sender_transfer_limits()
        self.resolved_date = datetime.datetime.utcnow()
        self.transfer_status = TransferStatusEnum.COMPLETE
        self.sender_transfer_account.decrement_balance(self.transfer_amount)
        self.recipient_transfer_account.increment_balance(self.transfer_amount)

        if self.transfer_type == TransferTypeEnum.PAYMENT and self.transfer_subtype == TransferSubTypeEnum.DISBURSEMENT:
            if self.recipient_user and self.recipient_user.transfer_card:
                self.recipient_user.transfer_card.update_transfer_card()

        if self.fiat_ramp and self.transfer_type in [TransferTypeEnum.DEPOSIT, TransferTypeEnum.WITHDRAWAL]:
            self.fiat_ramp.resolve_as_completed()
        if not existing_blockchain_txn:
            self.send_blockchain_payload_to_worker(queue=queue)

    def resolve_as_rejected(self, message=None):
        if self.fiat_ramp and self.transfer_type in [TransferTypeEnum.DEPOSIT, TransferTypeEnum.WITHDRAWAL]:
            self.fiat_ramp.resolve_as_rejected()

        self.resolved_date = datetime.datetime.utcnow()
        self.transfer_status = TransferStatusEnum.REJECTED

        if message:
            self.resolution_message = message

    def get_transfer_limits(self):
        import server.utils.transfer_limits

        return server.utils.transfer_limits.get_transfer_limits(self)

    def check_sender_transfer_limits(self):
        if self.sender_user is None:
            # skip if there is no sender, which implies system send
            return

        relevant_transfer_limits = self.get_transfer_limits()

        for limit in relevant_transfer_limits:

            if limit.no_transfer_allowed:
                raise NoTransferAllowedLimitError(token=self.token.name)

            if limit.transfer_count is not None:
                # GE Limits
                transaction_count = limit.apply_all_filters(
                    self,
                    db.session.query(func.count(CreditTransfer.id).label('count'))
                ).execution_options(show_all=True).first().count

                if (transaction_count or 0) > limit.transfer_count:
                    message = 'Account Limit "{}" reached. Allowed {} transaction per {} days'\
                        .format(limit.name, limit.transfer_count, limit.time_period_days)
                    self.resolve_as_rejected(message=message)
                    raise TransferCountLimitError(
                        transfer_count_limit=limit.transfer_count,
                        limit_time_period_days=limit.time_period_days,
                        token=self.token.name,
                        message=message
                    )

            if limit.transfer_balance_fraction is not None:
                allowed_transfer = limit.transfer_balance_fraction * self.sender_transfer_account.balance

                if self.transfer_amount > allowed_transfer:
                    message = 'Account % Limit "{}" reached. {} available'.format(
                        limit.name,
                        max(allowed_transfer, 0)
                    )
                    self.resolve_as_rejected(message=message)
                    raise TransferBalanceFractionLimitError(
                        transfer_balance_fraction_limit=limit.transfer_balance_fraction,
                        transfer_amount_avail=int(allowed_transfer),
                        limit_time_period_days=limit.time_period_days,
                        token=self.token.name,
                        message=message
                    )

            if limit.total_amount is not None:
                # Sempo Compliance Account Limits

                transaction_volume = limit.apply_all_filters(
                    self,
                    db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
                ).execution_options(show_all=True).first().total or 0

                if transaction_volume > limit.total_amount:
                    # Don't include the current transaction when reporting amount available
                    amount_avail = limit.total_amount - transaction_volume + int(self.transfer_amount)

                    message = 'Account Limit "{}" reached. {} available'.format(limit.name, max(amount_avail, 0))
                    self.resolve_as_rejected(message=message)
                    raise TransferAmountLimitError(
                        transfer_amount_limit=limit.total_amount,
                        transfer_amount_avail=amount_avail,
                        limit_time_period_days=limit.time_period_days,
                        token=self.token.name,
                        message=message
                    )

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
        self.transfer_metadata = transfer_metadata

        if uuid is not None:
            self.uuid = uuid

        self.append_organisation_if_required(self.recipient_transfer_account.organisation)
        self.append_organisation_if_required(self.sender_transfer_account.organisation)
