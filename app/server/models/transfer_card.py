from flask import current_app
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func

from server import db
from server.models.utils import ModelBase
import server.models.credit_transfer
from server.utils.transfer_enums import TransferTypeEnum, TransferStatusEnum, TransferSubTypeEnum
from server.exceptions import NoTransferCardError


class TransferCard(ModelBase):
    __tablename__ = 'transfer_card'

    public_serial_number    = db.Column(db.String, index=True, unique=True, nullable=False)
    nfc_serial_number       = db.Column(db.String)
    PIN                     = db.Column(db.String)
    _is_disabled             = db.Column(db.Boolean, default=False)

    _amount_loaded          = db.Column(db.Integer)
    _amount_offset           = db.Column(db.Integer)

    amount_loaded_signature = db.Column(db.String)

    user_id                 = db.Column(db.Integer, db.ForeignKey("user.id"))
    transfer_account_id     = db.Column(db.Integer, db.ForeignKey("transfer_account.id"))


    credit_transfers = db.relationship(
        'CreditTransfer',
        backref='transfer_card',
        lazy='dynamic',
        foreign_keys='CreditTransfer.sender_transfer_card_id'
    )

    def disable(self):
        # disabling cards is permanent, hence no setter to enable a disabled card
        self._is_disabled = True

    @hybrid_property
    def is_disabled(self):
        return self._is_disabled

    @hybrid_property
    def amount_loaded(self):
        return self._amount_loaded

    @amount_loaded.setter
    def amount_loaded(self, amount):
        self._amount_loaded = round(amount)
        message = '{}{}{}'.format(
            self.nfc_serial_number,
            self._amount_loaded,
            self.transfer_account.token.symbol
        )

        self.amount_loaded_signature = current_app.config['ECDSA_SIGNING_KEY'].sign(message.encode()).hex()

    @hybrid_property
    def amount_offset(self):
        return self._amount_offset

    @amount_offset.setter
    def amount_offset(self, amount):
        self._amount_offset = round(amount)
        self.update_transfer_card()

    @staticmethod
    def get_transfer_card(public_serial_number):
        transfer_card = TransferCard.query.filter_by(
            public_serial_number=public_serial_number).first()

        if not transfer_card:
            raise NoTransferCardError("No transfer card found for public serial number {}"
                                      .format(public_serial_number))

        return transfer_card

    def update_transfer_card(self):
        # All credits into this account
        credits_in = (
            db.session.query(
                func.sum(server.models.credit_transfer.CreditTransfer._transfer_amount_wei).label('total')
            ).execution_options(show_all=True)
                .filter_by(recipient_transfer_account=self.transfer_account)
                .filter_by(transfer_status=TransferStatusEnum.COMPLETE)
                .scalar() or 0
        )

        # All credits out of this account that did NOT originate from the card
        non_card_credits_out = (
            db.session.query(
                func.sum(server.models.credit_transfer.CreditTransfer._transfer_amount_wei).label('total')
            ).execution_options(show_all=True)
                .filter_by(sender_transfer_account=self.transfer_account)
                .filter_by(transfer_status=TransferStatusEnum.COMPLETE)
                .filter(server.models.credit_transfer.CreditTransfer.transfer_card != self)
                .scalar() or 0
        )

        self.amount_loaded = int((credits_in - non_card_credits_out)/int(1e16)) + (self.amount_offset or 0)
