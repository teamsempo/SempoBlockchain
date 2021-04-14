from server import db
from sqlalchemy import func

from server.models.utils import ModelBase, OneOrgBase, disbursement_transfer_account_association_table,\
    disbursement_credit_transfer_association_table
from sqlalchemy.types import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property

ALLOWED_STATES = ['PENDING', 'APPROVED', 'REJECTED']
ALLOWED_STATE_TRANSITIONS = {
    'PENDING': ['APPROVED', 'REJECTED']
}

class Disbursement(ModelBase):
    __tablename__ = 'disbursement'

    creator_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    label = db.Column(db.String)
    search_string = db.Column(db.String)
    search_filter_params = db.Column(db.String)
    include_accounts = db.Column(db.ARRAY(db.Integer))
    exclude_accounts = db.Column(db.ARRAY(db.Integer))
    state = db.Column(db.String)
    transfer_type = db.Column(db.String)
    _disbursement_amount_wei = db.Column(db.Numeric(27), default=0)

    creator_user = db.relationship('User',
                                    primaryjoin='User.id == Disbursement.creator_user_id')

    transfer_accounts = db.relationship(
        "TransferAccount",
        secondary=disbursement_transfer_account_association_table,
        back_populates="disbursements")

    credit_transfers = db.relationship(
        "CreditTransfer",
        secondary=disbursement_credit_transfer_association_table,
        back_populates="disbursement")

    @hybrid_property
    def recipient_count(self):
        return db.session.query(func.count(disbursement_transfer_account_association_table.c.disbursement_id==self.id)).first()[0]

    @hybrid_property
    def total_disbursement_amount(self):
        return db.session.query(func.count(disbursement_transfer_account_association_table.c.disbursement_id==self.id)).first()[0] * self._disbursement_amount_wei

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

    def approve(self):
        self._transition_state('APPROVED')

    def reject(self):
        self._transition_state('REJECTED')

    def __init__(self, *args, **kwargs):

        super(Disbursement, self).__init__(*args, **kwargs)

        self.state = 'PENDING'
