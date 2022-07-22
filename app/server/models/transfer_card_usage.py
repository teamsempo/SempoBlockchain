from flask import current_app
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from sqlalchemy.orm import backref

from server import db
from server.models.utils import ModelBase
from server.models.transfer_card import TransferCard
from server.models.credit_transfer import CreditTransfer

class TransferCardUsage(ModelBase):
    __tablename__ = 'transfer_card_usage'
    # Vendor account
    vendor_transfer_account_id       = db.Column(db.Integer, db.ForeignKey("transfer_account.id"), index=True)
    vendor_transfer_account          = db.relationship('TransferAccount', foreign_keys=[vendor_transfer_account_id], lazy='select')

    # Transfer card
    transfer_card_id       = db.Column(db.Integer, db.ForeignKey("transfer_card.id"), index=True)
    transfer_card          = db.relationship('TransferCard', foreign_keys=[transfer_card_id], backref='transfer_card_usages', lazy='select')

    # Credit transfer
    credit_transfer_id       = db.Column(db.Integer, db.ForeignKey("credit_transfer.id"), index=True)
    credit_transfer          = db.relationship('CreditTransfer', foreign_keys=[credit_transfer_id], backref=backref('transfer_card_usage', uselist=False), lazy='select')
