from flask import current_app
from sqlalchemy.ext.hybrid import hybrid_property

from server import db
from server.models.utils import ModelBase
import server.models.credit_transfer
from server.utils.transfer_enums import TransferTypeEnum, TransferStatusEnum, TransferSubTypeEnum
from server.exceptions import NoTransferCardError


class TransferCard(ModelBase):
    __tablename__ = 'transfer_card'

    public_serial_number = db.Column(db.String, index=True, unique=True, nullable=False)
    nfc_serial_number    = db.Column(db.String)
    PIN                  = db.Column(db.String)

    _amount_loaded          = db.Column(db.Integer)
    amount_loaded_signature = db.Column(db.String)

    user_id    = db.Column(db.Integer, db.ForeignKey("user.id"))

    transfer_account_id    = db.Column(db.Integer, db.ForeignKey("transfer_account.id"))

    @hybrid_property
    def amount_loaded(self):
        return self._phone

    @amount_loaded.setter
    def amount_loaded(self, amount):
        self._amount_loaded = round(amount)
        message = '{}{}{}'.format(
            self.nfc_serial_number,
            self._amount_loaded,
            self.transfer_account.token.symbol
        )

        self.amount_loaded_signature = current_app.config['ECDSA_SIGNING_KEY'].sign(message.encode()).hex()

    @staticmethod
    def get_transfer_card(public_serial_number):
        transfer_card = TransferCard.query.filter_by(
            public_serial_number=public_serial_number).first()

        if not transfer_card:
            raise NoTransferCardError("No transfer card found for public serial number {}"
                                      .format(public_serial_number))

        return transfer_card

    def update_transfer_card(self):
        disbursements = (server.models.credit_transfer.CreditTransfer.query
                         .execution_options(show_all=True)
                         .filter_by(recipient_user_id=self.user_id)
                         .filter_by(transfer_type=TransferTypeEnum.PAYMENT)
                         .filter_by(transfer_subtype=TransferSubTypeEnum.DISBURSEMENT)
                         .filter_by(transfer_status=TransferStatusEnum.COMPLETE)
                         .all())

        total_disbursed = 0

        for disbursement in disbursements:
            total_disbursed += float(disbursement.transfer_amount)

        self.amount_loaded = total_disbursed
