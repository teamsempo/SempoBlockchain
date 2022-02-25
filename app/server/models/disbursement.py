from server import db
from flask import g, current_app
from sqlalchemy import func
import datetime
from server.models.utils import ModelBase, OneOrgBase, disbursement_transfer_account_association_table,\
    disbursement_credit_transfer_association_table, disbursement_approver_user_association_table
from sqlalchemy.ext.hybrid import hybrid_property
from server.utils.access_control import AccessControl

PENDING = 'PENDING'
APPROVED = 'APPROVED'
PARTIAL = 'PARTIAL'
REJECTED = 'REJECTED'

ALLOWED_STATES = [PENDING, APPROVED, PARTIAL, REJECTED]
ALLOWED_STATE_TRANSITIONS = {
    PENDING: [APPROVED, PARTIAL, REJECTED],
    PARTIAL: [APPROVED, REJECTED, PARTIAL]
}

class Disbursement(ModelBase, OneOrgBase):
    __tablename__ = 'disbursement'

    creator_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    label = db.Column(db.String)
    notes = db.Column(db.String(), default='')
    errors = db.Column(db.ARRAY(db.String), default=[])
    search_string = db.Column(db.String)
    search_filter_params = db.Column(db.String)
    include_accounts = db.Column(db.ARRAY(db.Integer))
    exclude_accounts = db.Column(db.ARRAY(db.Integer))
    state = db.Column(db.String)
    transfer_type = db.Column(db.String)
    _disbursement_amount_wei = db.Column(db.Numeric(27), default=0)

    creator_user = db.relationship('User',
                                    primaryjoin='User.id == Disbursement.creator_user_id',
                                    lazy=True)

    transfer_accounts = db.relationship(
        "TransferAccount",
        secondary=disbursement_transfer_account_association_table,
        back_populates="disbursements",
        lazy=True)

    credit_transfers = db.relationship(
        "CreditTransfer",
        secondary=disbursement_credit_transfer_association_table,
        back_populates="disbursement",
        lazy=True)

    approvers = db.relationship(
        "User",
        secondary=disbursement_approver_user_association_table,
        lazy=True
    )
    approval_times = db.Column(db.ARRAY(db.DateTime), default=[])
    
    @hybrid_property
    def recipient_count(self):
        return db.session.query(func.count(disbursement_transfer_account_association_table.c.disbursement_id))\
            .filter(disbursement_transfer_account_association_table.c.disbursement_id==self.id).first()[0]

    @hybrid_property
    def total_disbursement_amount(self):
        return self.recipient_count * self.disbursement_amount 

    @hybrid_property
    def disbursement_amount(self):
        return (self._disbursement_amount_wei or 0) / int(1e16)

    @disbursement_amount.setter
    def disbursement_amount(self, val):
        self._disbursement_amount_wei = val * int(1e16)

    def _transition_state(self, new_state):
        if new_state not in ALLOWED_STATES:
            raise Exception(f'{new_state} is not an allowed state, must be one of f{ALLOWED_STATES}')

        allowed_transitions = ALLOWED_STATE_TRANSITIONS.get(self.state, [])

        if new_state not in allowed_transitions:
            raise Exception(f'{new_state} is not an allowed transition, must be one of f{allowed_transitions}')

        self.state = new_state

    def add_approver(self):
        if g.user not in self.approvers:
            if not self.approval_times:
                self.approval_times = []
            if len(self.approvers) == len(self.approval_times):
                self.approval_times = self.approval_times + [datetime.datetime.utcnow()] 
            self.approvers.append(g.user)
        
    def check_if_approved(self):
        if AccessControl.has_sufficient_tier(g.user.roles, 'ADMIN', 'sempoadmin'):
            return True
        if current_app.config['REQUIRE_MULTIPLE_APPROVALS']:
            # It always has to be approved by at least two people
            if len(self.approvers) <=1:
                return False
            # If there's an `ALLOWED_APPROVERS` list, one of the approvers has to be in it
            if current_app.config['ALLOWED_APPROVERS']:
                # approve if email in list
                for user in self.approvers:
                    if user.email in current_app.config['ALLOWED_APPROVERS']:
                        return True
            # If there's not an `ALLOWED_APPROVERS` list, it just has to be approved by more than one person
            else:
                return True
        else:
            # Multi-approval is off, so it's approved by default
            return True

    def approve(self):
        self.add_approver()
        if self.check_if_approved():
            self._transition_state(APPROVED)
        else:
            self._transition_state(PARTIAL)
            return PARTIAL

    def reject(self):
        self.add_approver()             
        self._transition_state(REJECTED)

    def __init__(self, *args, **kwargs):
        self.organisation_id = g.active_organisation.id
        super(Disbursement, self).__init__(*args, **kwargs)
        self.state = PENDING
