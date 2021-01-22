from server import db
from server.models.utils import ModelBase, OneOrgBase, disbursement_transfer_account_association_table,\
    disbursement_credit_transfer_association_table
from sqlalchemy.types import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
class Disbursement(ModelBase):
    __tablename__ = 'disbursement'

    creator_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    search_string = db.Column(db.String)
    search_filter_params = db.Column(db.String)
    include_accounts = db.Column(db.ARRAY(db.Integer))
    exclude_accounts = db.Column(db.ARRAY(db.Integer))
    is_executed = db.Column(db.Boolean)
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
    def disbursement_amount(self):
        return (self._disbursement_amount_wei or 0) / int(1e16)

    @disbursement_amount.setter
    def disbursement_amount(self, val):
        self._disbursement_amount_wei = val * int(1e16)
