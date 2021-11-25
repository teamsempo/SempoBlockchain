from typing import Optional, Union
from decimal import Decimal
import datetime, enum
from flask import g

from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import or_

from server import db, bt
from server.models.utils import ModelBase, OneOrgBase, user_transfer_account_association_table, \
    get_authorising_user_id, SoftDelete, disbursement_transfer_account_association_table
from server.models.user import User
from server.models.spend_approval import SpendApproval
from server.models.exchange import ExchangeContract
from server.models.organisation import Organisation
import server.models.credit_transfer
from server.exceptions import TransferAccountDeletionError, ResourceAlreadyDeletedError
from server.models.audit_history import track_updates

from server.utils.transfer_enums import TransferStatusEnum, TransferSubTypeEnum, TransferModeEnum


class TransferAccountType(enum.Enum):
    USER            = 'USER'
    ORGANISATION    = 'ORGANISATION'
    FLOAT           = 'FLOAT'
    CONTRACT        = 'CONTRACT'
    EXTERNAL        = 'EXTERNAL'


class TransferAccount(OneOrgBase, ModelBase, SoftDelete):
    __tablename__ = 'transfer_account'
    audit_history_columns = [
        'name',
        'blockchain_address',
        'is_approved',
        'account_type',
        'notes'
    ]

    name            = db.Column(db.String())
    _balance_wei    = db.Column(db.Numeric(27), default=0, index=True)

    # override ModelBase deleted to add an index
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

    # The purpose of the balance offset is to allow the master wallet to be seeded at
    # initial deploy time. Since balance is calculated by subtracting total credits from
    # total debits, without a balance offset we'd be stuck in a zero-sum system with no
    # mechanism to have initial funds. It's essentially an app-level analogy to minting
    # which happens on the chain.
    _balance_offset_wei    = db.Column(db.Numeric(27), default=0)
    blockchain_address = db.Column(db.String())

    is_approved     = db.Column(db.Boolean, default=False)

    # These are different from the permissions on the user:
    # is_vendor determines whether the account is allowed to have cash out operations etc
    # is_beneficiary determines whether the account is included in disbursement lists etc
    is_vendor       = db.Column(db.Boolean, default=False)

    is_beneficiary = db.Column(db.Boolean, default=False)

    is_ghost = db.Column(db.Boolean, default=False)

    account_type    = db.Column(db.Enum(TransferAccountType), index=True)

    payable_period_type   = db.Column(db.String(), default='week')
    payable_period_length = db.Column(db.Integer, default=2)
    payable_epoch         = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    token_id        = db.Column(db.Integer, db.ForeignKey("token.id"), index=True)

    exchange_contract_id = db.Column(db.Integer, db.ForeignKey(ExchangeContract.id))

    transfer_card    = db.relationship('TransferCard', backref='transfer_account', lazy=True, uselist=False)

    notes            = db.Column(db.String(), default='')

    # users               = db.relationship('User', backref='transfer_account', lazy=True)
    users = db.relationship(
        "User",
        secondary=user_transfer_account_association_table,
        back_populates="transfer_accounts",
        lazy='joined'
    )

    disbursements = db.relationship(
        "Disbursement",
        secondary=disbursement_transfer_account_association_table,
        back_populates="transfer_accounts",
        lazy='joined'
    )
    credit_sends = db.relationship(
        'CreditTransfer',
        foreign_keys='CreditTransfer.sender_transfer_account_id',
        back_populates='sender_transfer_account',
        order_by='desc(CreditTransfer.id)'
    )

    credit_receives = db.relationship(
        'CreditTransfer',
        foreign_keys='CreditTransfer.recipient_transfer_account_id',
        back_populates='recipient_transfer_account',
        order_by='desc(CreditTransfer.id)'
    )

    spend_approvals_given = db.relationship('SpendApproval', backref='giving_transfer_account',
                                            foreign_keys='SpendApproval.giving_transfer_account_id')

    def delete_transfer_account_from_user(self, user: User):
        """
        Soft deletes a Transfer Account if no other users associated to it.
        """
        try:
            if self.balance != 0:
                raise TransferAccountDeletionError('Balance must be zero to delete')
            if self.total_sent_incl_pending_wei != self.total_sent_complete_only_wei:
                raise TransferAccountDeletionError('Must resolve pending transactions before account deletion')
            if len(self.users) > 1:
                # todo(user): deletion of user from account with multiple users - NOT CURRENTLY SUPPORTED
                raise TransferAccountDeletionError('More than one user attached to transfer account')
            if self.primary_user == user:
                timenow = datetime.datetime.utcnow()
                self.deleted = timenow
            else:
                raise TransferAccountDeletionError('Primary user does not match provided user')

        except (ResourceAlreadyDeletedError, TransferAccountDeletionError) as e:
            raise e

    @property
    def unrounded_balance(self):
        return Decimal(self._balance_wei or 0) / Decimal(1e16)

    @property
    def balance(self):
        # division/multipication by int(1e16) occurs  because
        # the db stores amounts in integer WEI: 1 BASE-UNIT (ETH/USD/ETC) * 10^18
        # while the system passes around amounts in float CENTS: 1 BASE-UNIT (ETH/USD/ETC) * 10^2
        # Therefore the conversion between db and system is 10^18/10^2c = 10^16
        # We use cents for historical reasons, and to enable graceful degredation/rounding on
        # hardware that can only handle small ints (like the transfer cards and old android devices)

        # rounded to whole value of balance
        return Decimal((self._balance_wei or 0) / int(1e16))

    @property
    def balance_offset(self):
        return Decimal((self._balance_offset_wei or 0) / int(1e16))

    def set_balance_offset(self, val):
        self._balance_offset_wei = val * int(1e16)
        self.update_balance()

    def update_balance(self):
        """
        Update the balance of the user by calculating the difference between inbound and outbound transfers, plus an
        offset.
        For inbound transfers we count ONLY complete, while for outbound we count both COMPLETE and PENDING.
        This means that users can't spend funds that are potentially:
        - already spent
        or
        - from a transfer that may ultimately be rejected.
        """
        if not self._balance_offset_wei:
            self._balance_offset_wei = 0

        net_credit_transfer_position_wei = (
                self.total_received_complete_only_wei - self.total_sent_incl_pending_wei
        )

        self._balance_wei = net_credit_transfer_position_wei + self._balance_offset_wei

    @hybrid_property
    def total_sent(self):
        """
        Canonical total sent in cents, helping us to remember that sent amounts should include pending txns
        """
        return Decimal(self.total_sent_incl_pending_wei) / int(1e16)

    @hybrid_property
    def total_received(self):
        """
        Canonical total sent in cents, helping us to remember that received amounts should only include complete txns
        """
        return Decimal(self.total_received_complete_only_wei) / int(1e16)

    @hybrid_property
    def total_sent_complete_only_wei(self):
        """
        The total sent by an account, counting ONLY transfers that have been resolved as complete locally
        """
        amount = (
            db.session.query(
                func.sum(server.models.credit_transfer.CreditTransfer._transfer_amount_wei).label('total')
            )
                .execution_options(show_all=True)
                .filter(server.models.credit_transfer.CreditTransfer.sender_transfer_account_id == self.id)
                .filter(server.models.credit_transfer.CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE)
                .first().total
        )
        return amount or 0

    @hybrid_property
    def total_received_complete_only_wei(self):
        """
        The total received by an account, counting ONLY transfers that have been resolved as complete
        """
        amount = (
            db.session.query(
                func.sum(server.models.credit_transfer.CreditTransfer._transfer_amount_wei).label('total')
            )
                .execution_options(show_all=True)
                .filter(server.models.credit_transfer.CreditTransfer.recipient_transfer_account_id == self.id)
                .filter(server.models.credit_transfer.CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE)
                .first().total
        )

        return amount or 0

    @hybrid_property
    def total_sent_incl_pending_wei(self):
        """
        The total sent by an account, counting transfers that are either pending or complete locally
        """
        amount = (
                db.session.query(
                    func.sum(server.models.credit_transfer.CreditTransfer._transfer_amount_wei).label('total')
                )
                .execution_options(show_all=True)
                .filter(server.models.credit_transfer.CreditTransfer.sender_transfer_account_id == self.id)
                .filter(or_(
                    server.models.credit_transfer.CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
                    server.models.credit_transfer.CreditTransfer.transfer_status == TransferStatusEnum.PARTIAL,
                    server.models.credit_transfer.CreditTransfer.transfer_status == TransferStatusEnum.PENDING))
                .first().total
        )
        return amount or 0

    @hybrid_property
    def total_received_incl_pending_wei(self):
        """
        The total received by an account, counting transfers that are either pending or complete locally
        """
        amount = (
            db.session.query(
                func.sum(server.models.credit_transfer.CreditTransfer._transfer_amount_wei).label('total')
            )
                .execution_options(show_all=True)
                .filter(server.models.credit_transfer.CreditTransfer.recipient_transfer_account_id == self.id)
                .filter(or_(
                server.models.credit_transfer.CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
                server.models.credit_transfer.CreditTransfer.transfer_status == TransferStatusEnum.PARTIAL,
                server.models.credit_transfer.CreditTransfer.transfer_status == TransferStatusEnum.PENDING))
                .first().total
        )
        return amount or 0

    @hybrid_property
    def primary_user(self):
        if len(self.users) == 0:
            return None
        return self.users[0]
        # users = User.query.execution_options(show_all=True) \
        #     .filter(User.transfer_accounts.any(TransferAccount.id.in_([self.id]))).all()
        # if len(users) == 0:
        #     # This only happens when we've unbound a user from a transfer account by manually editing the db
        #     return None
        #
        # return sorted(users, key=lambda user: user.created)[0]

    @hybrid_property
    def primary_user_id(self):
        return self.primary_user.id

    # rounded balance
    @hybrid_property
    def rounded_account_balance(self):
        return (self._balance_wei or 0) / int(1e18)

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

    def approve_initial_disbursement(self):
        from server.utils.access_control import AccessControl

        admin = getattr(g, 'user', None)
        active_org = getattr(g, 'active_organisation', Organisation.master_organisation())

        initial_disbursement = db.session.query(server.models.credit_transfer.CreditTransfer)\
            .filter(server.models.credit_transfer.CreditTransfer.recipient_user == self.primary_user)\
            .filter(server.models.credit_transfer.CreditTransfer.is_initial_disbursement == True)\
            .first()
        
        if initial_disbursement and initial_disbursement.transfer_status == TransferStatusEnum.PENDING:
            # Must be superadmin to auto-resolve something over default disbursement
            if initial_disbursement.transfer_amount > active_org.default_disbursement:
                if admin and AccessControl.has_sufficient_tier(admin.roles, 'ADMIN', 'superadmin'):
                    return initial_disbursement.resolve_as_complete_and_trigger_blockchain(queue='high-priority')
                else:
                    return False
            else:
                return initial_disbursement.resolve_as_complete_and_trigger_blockchain(queue='high-priority')

    def approve_and_disburse(self, initial_disbursement=None):
        from server.utils.access_control import AccessControl
        admin = getattr(g, 'user', None)
        active_org = getattr(g, 'active_organisation', Organisation.master_organisation())
        
        if initial_disbursement is None:
            # initial disbursement defaults to None. If initial_disbursement is set then skip this section.
            # If none, then we want to see if the active_org has a default disbursement amount
            initial_disbursement = active_org.default_disbursement

        # Baseline is NOT is_approved, and do NOT auto_resolve
        self.is_approved = False
        auto_resolve = False
        # If admin role is admin or higher, then auto-approval is contingent on being less than or 
        # equal to the default disbursement
        if (admin and AccessControl.has_sufficient_tier(admin.roles, 'ADMIN', 'admin'))or (
            g.get('auth_type') == 'external' and active_org.auto_approve_externally_created_users
        ):
            self.is_approved = True
            if initial_disbursement <= active_org.default_disbursement:
                auto_resolve = True
                
        # Accounts created by superadmins are all approved, and their disbursements are 
        # auto-resolved no matter how big they are!
        if admin and AccessControl.has_sufficient_tier(admin.roles, 'ADMIN', 'superadmin'):
            self.is_approved = True
            auto_resolve = True

        if self.is_beneficiary:
            # Initial disbursement should be pending if the account is not approved
            disbursement = self._make_initial_disbursement(initial_disbursement, auto_resolve=auto_resolve)
            return disbursement

    def _make_initial_disbursement(self, initial_disbursement=None, auto_resolve=None):
        from server.utils.credit_transfer import make_payment_transfer
       
        if not initial_disbursement:
            # if initial_disbursement is still none, then we don't want to create a transfer.
            return None

        user_id = get_authorising_user_id()
        if user_id is not None:
            sender = User.query.execution_options(show_all=True).get(user_id)
        else:
            sender = self.primary_user

        disbursement = make_payment_transfer(
            initial_disbursement, token=self.token, send_user=sender, receive_user=self.primary_user,
            transfer_subtype=TransferSubTypeEnum.DISBURSEMENT, transfer_mode=TransferModeEnum.WEB,
            is_ghost_transfer=False, require_sender_approved=False,
            require_recipient_approved=False, automatically_resolve_complete=auto_resolve)
        disbursement.is_initial_disbursement = True
        return disbursement

    def initialise_withdrawal(self, withdrawal_amount, transfer_mode):
        from server.utils.credit_transfer import make_withdrawal_transfer
        withdrawal = make_withdrawal_transfer(withdrawal_amount,
                                              send_user=self,
                                              automatically_resolve_complete=False,
                                              transfer_mode=transfer_mode,
                                              token=self.token)
        return withdrawal

    def _bind_to_organisation(self, organisation):
        if not self.organisation:
            self.organisation = organisation
        if not self.token:
            self.token = organisation.token

    def __init__(self,
                 blockchain_address: Optional[str]=None,
                 bound_entity: Optional[Union[Organisation, User]]=None,
                 account_type: Optional[TransferAccountType]=None,
                 private_key: Optional[str] = None,
                 **kwargs):

        super(TransferAccount, self).__init__(**kwargs)

        if bound_entity:
            bound_entity.transfer_accounts.append(self)

            if isinstance(bound_entity, Organisation):
                self.account_type = TransferAccountType.ORGANISATION
                self.blockchain_address = bound_entity.primary_blockchain_address

                self._bind_to_organisation(bound_entity)

            elif isinstance(bound_entity, User):
                self.account_type = TransferAccountType.USER
                self.blockchain_address = bound_entity.primary_blockchain_address

                if bound_entity.default_organisation:
                    self._bind_to_organisation(bound_entity.default_organisation)

            elif isinstance(bound_entity, ExchangeContract):
                self.account_type = TransferAccountType.CONTRACT
                self.blockchain_address = bound_entity.blockchain_address
                self.is_public = True
                self.exchange_contact = self

        if not self.organisation:
            master_organisation = Organisation.master_organisation()
            if not master_organisation:
                print('master_organisation not found')
            if master_organisation:
                self._bind_to_organisation(master_organisation)

        if blockchain_address:
            self.blockchain_address = blockchain_address

        if not self.blockchain_address:
            self.blockchain_address = bt.create_blockchain_wallet(private_key=private_key)

        if account_type:
            self.account_type = account_type

track_updates(TransferAccount)
