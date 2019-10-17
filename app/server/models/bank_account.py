from server import db
from server.models.utils import ModelBase


class BankAccount(ModelBase):
    __tablename__ = 'bank_account'

    # Wyre SRN
    wyre_id = db.Column(db.String)

    kyc_application_id = db.Column(
        db.Integer, db.ForeignKey('kyc_application.id'))

    bank_country = db.Column(db.String)
    routing_number = db.Column(db.String)
    account_number = db.Column(db.String)
    currency = db.Column(db.String)
