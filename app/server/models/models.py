from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import JSON
import datetime, random, string

from server.exceptions import (
    IconNotSupportedException
)
from server.constants import (
    MATERIAL_COMMUNITY_ICONS
)
from server import db
from server.utils.blockchain_tasks import (
    get_token_decimals
)
from server.models.utils import ModelBase, OneOrgBase


class ChatbotState(ModelBase):
    __tablename__ = 'chatbot_state'

    transfer_initialised = db.Column(db.Boolean, default=False)
    target_user_id = db.Column(db.Integer, default=None)
    transfer_amount = db.Column(db.Integer, default=0)
    prev_pin_failures = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    provider_message_id = db.Column(db.String())

    user = db.relationship(
        'User', backref='chatbot_state', lazy=True, uselist=False)


class Token(ModelBase):
    __tablename__ = 'token'

    address = db.Column(db.String, index=True, unique=True, nullable=False)
    name = db.Column(db.String)
    symbol = db.Column(db.String)
    _decimals = db.Column(db.Integer)

    organisations = db.relationship('Organisation',
                                    backref='token',
                                    lazy=True,
                                    foreign_keys='Organisation.token_id')

    transfer_accounts = db.relationship('TransferAccount', backref='token', lazy=True,
                                        foreign_keys='TransferAccount.token_id')

    credit_transfers = db.relationship('CreditTransfer', backref='token', lazy=True,
                                       foreign_keys='CreditTransfer.token_id')

    approvals = db.relationship('SpendApproval', backref='token', lazy=True,
                                foreign_keys='SpendApproval.token_id')

    @property
    def decimals(self):
        if self._decimals:
            return self._decimals

        decimals_from_contract_definition = get_token_decimals(self)

        if decimals_from_contract_definition:
            return decimals_from_contract_definition

        raise Exception("Decimals not defined in either database or contract")

    def token_amount_to_system(self, token_amount):
        return int(token_amount) * 100 / 10**self.decimals

    def system_amount_to_token(self, system_amount):
        return int(float(system_amount) / 100 * 10**self.decimals)


class TargetingSurvey(ModelBase):
    __tablename__ = 'targeting_survey'

    number_people_household = db.Column(db.Integer)
    number_below_adult_age_household = db.Column(db.Integer)
    number_people_women_household = db.Column(db.Integer)
    number_people_men_household = db.Column(db.Integer)
    number_people_work_household = db.Column(db.Integer)
    disabilities_household = db.Column(db.String)
    long_term_illnesses_household = db.Column(db.String)

    user = db.relationship(
        'User', backref='targeting_survey', lazy=True, uselist=False)


class CurrencyConversion(ModelBase):
    __tablename__ = 'currency_conversion'

    code = db.Column(db.String)
    rate = db.Column(db.Float)


class Settings(ModelBase):
    __tablename__ = 'settings'

    name = db.Column(db.String)
    type = db.Column(db.String)
    value = db.Column(JSON)


class BlacklistToken(ModelBase):
    """
    Token Model for storing JWT tokens
    """
    __tablename__ = 'blacklist_tokens'

    token = db.Column(db.String(500), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def check_blacklist(auth_token):
        # check whether auth token has been blacklisted
        res = BlacklistToken.query.filter_by(token=str(auth_token)).first()
        if res:
            return True
        else:
            return False

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.datetime.now()

    def __repr__(self):
        return '<id: token: {}'.format(self.token)


class EmailWhitelist(OneOrgBase, ModelBase):
    __tablename__ = 'email_whitelist'

    email = db.Column(db.String)

    tier = db.Column(db.String, default='view')
    referral_code = db.Column(db.String)

    allow_partial_match = db.Column(db.Boolean, default=False)
    used = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super(EmailWhitelist, self).__init__(**kwargs)
        self.referral_code = ''.join(random.choices(
            string.ascii_letters + string.digits, k=16))


class SavedFilter(ModelBase):
    __tablename__ = 'saved_filter'

    name = db.Column(db.String)
    filter = db.Column(JSON)


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


class TransferUsage(ModelBase):
    __tablename__ = 'transfer_usage'

    name = db.Column(db.String)
    is_cashout = db.Column(db.Boolean)
    _icon = db.Column(db.String)
    priority = db.Column(db.Integer)
    translations = db.Column(JSON)

    @hybrid_property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, icon):
        if icon not in MATERIAL_COMMUNITY_ICONS:
            raise IconNotSupportedException('Icon {} not supported or found')
        self._icon = icon


class CustomAttribute(ModelBase):
    __tablename__ = 'custom_attribute'

    name = db.Column(db.String)
