from sqlalchemy.dialects.postgresql import JSON

from server import db
from server.models.utils import ModelBase
from server.models.user import User
from server.models.organisation import Organisation
from server.constants import (
    ALLOWED_KYC_TYPES
)
from server.exceptions import (
    TypeNotFoundException
)


class KycApplication(ModelBase):
    __tablename__       = 'kyc_application'

    # compliance
    trulioo_id          = db.Column(db.String)
    namescan_scan_id    = db.Column(db.String)

    # Wyre SRN
    wyre_id             = db.Column(db.String)

    # todo: convert to enum
    # Either "INCOMPLETE", "PENDING", "VERIFIED" or "REJECTED"
    kyc_status          = db.Column(db.String, default='INCOMPLETE')

    # returns array. action items for mobile and internal use. ['non_valid','id_blurry','no_match_selfie']
    kyc_actions         = db.Column(JSON)
    kyc_attempts        = db.Column(db.Integer)

    # INDIVIDUAL or BUSINESS... MASTER (deprecated)
    type                = db.Column(db.String)

    first_name          = db.Column(db.String)
    last_name           = db.Column(db.String)
    phone               = db.Column(db.String)
    dob                 = db.Column(db.String)
    business_legal_name = db.Column(db.String)
    business_type       = db.Column(db.String)
    tax_id              = db.Column(db.String)
    website             = db.Column(db.String)
    date_established    = db.Column(db.String)
    country             = db.Column(db.String)
    street_address      = db.Column(db.String)
    street_address_2    = db.Column(db.String)
    city                = db.Column(db.String)
    region              = db.Column(db.String)
    postal_code         = db.Column(db.Integer)
    beneficial_owners   = db.Column(JSON)

    uploaded_documents = db.relationship('UploadedResource', backref='kyc_application', lazy=True,
                                         foreign_keys='UploadedResource.kyc_application_id')

    bank_accounts        = db.relationship('BankAccount', backref='kyc_application', lazy=True,
                                           foreign_keys='BankAccount.kyc_application_id')

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))

    organisation_id = db.Column(db.Integer, db.ForeignKey(Organisation.id))

    def __init__(self, type, **kwargs):
        super(KycApplication, self).__init__(**kwargs)
        if type not in ALLOWED_KYC_TYPES:
            raise TypeNotFoundException('Type {} not found')

        self.type = type
        self.kyc_attempts = 1

        if type == 'INDIVIDUAL':
            self.kyc_status = 'PENDING'