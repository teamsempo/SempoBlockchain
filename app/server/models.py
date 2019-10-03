import os, base64
from typing import Union
from contextlib import contextmanager
from eth_utils import keccak

from web3 import Web3
from sqlalchemy import event, inspect
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import JSON, INET, JSONB
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.query import Query
from cryptography.fernet import Fernet
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature, SignatureExpired
from flask import g, request, current_app
import datetime, bcrypt, jwt, enum, random, string
import pyotp

from server.exceptions import (
    RoleNotFoundException,
    TierNotFoundException,
    InvalidTransferTypeException,
    NoTransferAccountError,
    UserNotFoundError,
    NoTransferCardError,
    TypeNotFoundException,
    IconNotSupportedException,
    OrganisationNotProvidedException,
    PaymentMethodException
)

from server.constants import (
    ACCESS_ROLES,
    RANKED_ADMIN_TIERS,
    RANKED_VENDOR_TIERS,
    ALLOWED_KYC_TYPES,
    ALLOWED_BLOCKCHAIN_ADDRESS_TYPES,
    MATERIAL_COMMUNITY_ICONS,
    PAYMENT_METHODS
)
from server import db, sentry, celery_app
from server.utils.phone import proccess_phone_number
from server.utils.credit_transfers import make_disbursement_transfer, make_withdrawal_transfer
from server.utils.amazon_s3 import get_file_url
from server.utils.user import get_transfer_card
from server.utils.misc import elapsed_time, encrypt_string, decrypt_string, hex_private_key_to_address
from server.utils import auth
from server.utils.blockchain_tasks import (
    create_blockchain_wallet,
    get_token_decimals,
    send_eth,
    make_approval,
    make_token_transfer,
    get_blockchain_task
)


@contextmanager
def no_expire():
    s = db.session()
    s.expire_on_commit = False
    yield
    s.expire_on_commit = True

def paginate_query(query, queried_object=None, order_override=None):
    """
    Paginates an sqlalchemy query, gracefully managing missing queries.
    Default ordering is to show most recently created first.
    Unlike raw paginate, defaults to showing all results if args aren't supplied

    :param query: base query
    :param queried_object: underlying object being queried. Required to sort most recent
    :param order_override: override option for the sort parameter.
    :returns: tuple of (item list, total number of items, total number of pages)
    """

    page = request.args.get('page')
    per_page = request.args.get('per_page')

    if order_override:
        query = query.order_by(order_override)
    elif queried_object:
        query = query.order_by(queried_object.created.desc())

    if per_page is None:

        items = query.all()

        return items, len(items), 1

    if page is None:
        per_page = int(per_page)
        paginated = query.paginate(0, per_page, error_out=False)

        return paginated.items, paginated.total, paginated.pages

    per_page = int(per_page)
    page = int(page)

    paginated = query.paginate(page, per_page, error_out=False)

    return paginated.items, paginated.total, paginated.pages


def get_authorising_user_id():
    if hasattr(g,'user'):
        return g.user.id
    elif hasattr(g,'authorising_user_id'):
        return g.authorising_user_id
    else:
        return None


@event.listens_for(Query, "before_compile", retval=True)
def before_compile(query):
    """A query compilation rule that will add limiting criteria for every
    subclass of OrgBase"""

    show_all = getattr(g, "show_all", False) or query._execution_options.get("show_all", False)
    if show_all:
        return query

    for ent in query.column_descriptions:
        entity = ent['entity']
        if entity is None:
            continue
        insp = inspect(ent['entity'])
        mapper = getattr(insp, 'mapper', None)

        # if the subclass OrgBase exists, then filter by organisations - else, return default query
        if mapper:
            if issubclass(mapper.class_, ManyOrgBase) or issubclass(mapper.class_, OneOrgBase):

                try:
                    # member_organisations = getattr(g, "member_organisations", [])
                    active_organisation = getattr(g, "active_organisation_id", None)
                    member_organisations = [active_organisation] if active_organisation else []

                    if issubclass(mapper.class_, ManyOrgBase):
                        # filters many-to-many
                        query = query.enable_assertions(False).filter(
                            ent['entity'].organisations.any(Organisation.id.in_(member_organisations))
                        )
                    else:
                        query = query.enable_assertions(False).filter(
                            ent['entity'].organisation_id == active_organisation
                        )

                except AttributeError:
                    raise

                except TypeError:
                    raise OrganisationNotProvidedException('Must provide organisation ID or specify SHOW_ALL flag')

            elif issubclass(mapper.class_, OneOrgBase):
                # must filter directly on query
                raise OrganisationNotProvidedException('{} has a custom org base. Must filter directly on query'.format(ent['entity']))

    return query

# the recipe has a few holes in it, unfortunately, including that as given,
# it doesn't impact the JOIN added by joined eager loading.   As a guard
# against this and other potential scenarios, we can check every object as
# its loaded and refuse to continue if there's a problem

# @event.listens_for(OrgBase, "load", propagate=True)
# def load(obj, context):
    # todo: need to actually make this work...
    #  if not obj.organisations and not context.query._execution_options.get("show_all", False):
    #     raise TypeError(
    #         "organisation object %s was incorrectly loaded, did you use "
    #         "joined eager loading?" % obj)


class TransferTypeEnum(enum.Enum):
    PAYMENT      = "PAYMENT"
    DISBURSEMENT = "DISBURSEMENT"
    WITHDRAWAL   = "WITHDRAWAL"

class TransferModeEnum(enum.Enum):
    NFC = "NFC"
    SMS = "SMS"
    QR  = "QR"
    INTERNAL = "INTERNAL"
    OTHER    = "OTHER"

class TransferStatusEnum(enum.Enum):
    PENDING = 'PENDING'
    REJECTED = 'REJECTED'
    COMPLETE = 'COMPLETE'
    # PENDING = 0
    # INTERNAL_REJECTED = -1
    # INTERNAL_COMPLETE = 1
    # BLOCKCHAIN_REJECTED = -2
    # BLOCKCHAIN_COMPLETE = 2

class FiatRampStatusEnum(enum.Enum):
    PENDING = 'PENDING'
    FAILED = 'FAILED'
    COMPLETE = 'COMPLETE'

organisation_association_table = db.Table(
    'organisation_association_table',
    db.Model.metadata,
    db.Column('organisation_id', db.Integer, db.ForeignKey('organisation.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('transfer_account_id', db.Integer, db.ForeignKey('transfer_account.id')),
    db.Column('credit_transfer_id', db.Integer, db.ForeignKey('credit_transfer.id')),
)

user_transfer_account_association_table = db.Table(
    'user_transfer_account_association_table',
    db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('transfer_account_id', db.Integer, db.ForeignKey('transfer_account.id'))
)

class ModelBase(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    authorising_user_id = db.Column(db.Integer, default=get_authorising_user_id)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Organisation(ModelBase):
    """
    Establishes organisation object that resources can be associated with.
    """
    __tablename__       = 'organisation'

    name                = db.Column(db.String)

    system_blockchain_address = db.Column(db.String)

    users               = db.relationship(
                            "User",
                            secondary=organisation_association_table,
                            back_populates="organisations")

    token_id            = db.Column(db.Integer, db.ForeignKey('token.id'))


    org_level_transfer_account_id    = db.Column(db.Integer, db.ForeignKey('transfer_account.id', name="fk_org_level_account"))
    # We use this weird join pattern because SQLAlchemy
    # doesn't play nice when doing multiple joins of the same table over different declerative bases
    org_level_transfer_account       = db.relationship("TransferAccount",
                                                       post_update=True,
                                                       primaryjoin="Organisation.org_level_transfer_account_id==TransferAccount.id",
                                                       uselist=False)

    credit_transfers    = db.relationship(
                            "CreditTransfer",
                            secondary=organisation_association_table,
                            back_populates="organisations")

    transfer_accounts   = db.relationship('TransferAccount',
                                          backref='organisation',
                                          lazy=True, foreign_keys='TransferAccount.organisation_id')


    blockchain_addresses = db.relationship('BlockchainAddress', backref='organisation',
                                        lazy=True, foreign_keys='BlockchainAddress.organisation_id')

    email_whitelists    = db.relationship('EmailWhitelist', backref='organisation',
                                          lazy=True, foreign_keys='EmailWhitelist.organisation_id')


    def __init__(self, **kwargs):
        super(Organisation, self).__init__(**kwargs)

        self.system_blockchain_address = create_blockchain_wallet(
            wei_target_balance=current_app.config['SYSTEM_WALLET_TARGET_BALANCE'],
            wei_topup_threshold=current_app.config['SYSTEM_WALLET_TOPUP_THRESHOLD'],
        )


class OneOrgBase(object):
    """
    Mixin that automatically associates object(s) to organisation(s) many-to-one.

    Forces all database queries on associated objects to provide an organisation ID or specify show_all=True flag
    """

    @declared_attr
    def organisation_id(cls):
        return db.Column('organisation_id', db.ForeignKey('organisation.id'))


class ManyOrgBase(object):
    """
    Mixin that automatically associates object(s) to organisation(s) many-to-many.

    Forces all database queries on associated objects to provide an organisation ID or specify show_all=True flag
    """

    @declared_attr
    def organisations(cls):

        # pluralisation
        name = cls.__tablename__.lower()
        plural = name + 's'
        if name[-1] in ['s', 'sh', 'ch', 'x']:
            # exceptions to this rule...
            plural = name + 'es'

        return db.relationship("Organisation",
                               secondary=organisation_association_table,
                               back_populates=plural)

class User(ManyOrgBase, ModelBase):
    """Establishes the identity of a user for both making transactions and more general interactions.

        Admin users are created through the auth api by registering
        an account with an email that has been pre-approved on the whitelist.
        By default, admin users only have minimal access levels (view).
        Permissions must be elevated manually in the database.

        Transaction-capable users (vendors and beneficiaries) are
        created using the POST user API or the bulk upload function
    """
    __tablename__ = 'user'

    first_name      = db.Column(db.String())
    last_name       = db.Column(db.String())

    _last_seen       = db.Column(db.DateTime)

    email                   = db.Column(db.String())
    _phone                  = db.Column(db.String())
    _public_serial_number   = db.Column(db.String())
    nfc_serial_number       = db.Column(db.String())

    password_hash   = db.Column(db.String(128))
    one_time_code   = db.Column(db.String)
    secret          = db.Column(db.String())
    _TFA_secret     = db.Column(db.String(128))
    TFA_enabled     = db.Column(db.Boolean, default=False)

    default_currency = db.Column(db.String())

    _location       = db.Column(db.String())
    lat             = db.Column(db.Float())
    lng             = db.Column(db.Float())

    _held_roles = db.Column(JSONB)

    is_activated    = db.Column(db.Boolean, default=False)
    is_disabled     = db.Column(db.Boolean, default=False)
    is_phone_verified = db.Column(db.Boolean, default=False)
    is_self_sign_up = db.Column(db.Boolean, default=True)

    terms_accepted = db.Column(db.Boolean, default=True)

    custom_attributes = db.Column(JSON)
    matched_profile_pictures = db.Column(JSON)

    ap_user_id     = db.Column(db.String())
    ap_bank_id     = db.Column(db.String())
    ap_paypal_id   = db.Column(db.String())
    kyc_state      = db.Column(db.String())

    cashout_authorised = db.Column(db.Boolean, default=False)

    transfer_accounts = db.relationship(
        "TransferAccount",
        secondary=user_transfer_account_association_table,
        back_populates="users")

    chatbot_state_id    = db.Column(db.Integer, db.ForeignKey('chatbot_state.id'))
    targeting_survey_id = db.Column(db.Integer, db.ForeignKey('targeting_survey.id'))

    default_organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'))
    default_organisation    = db.relationship('Organisation',
                                              primaryjoin=Organisation.id==default_organisation_id,
                                              lazy=True,
                                              uselist=False)

    # roles = db.relationship('UserRole', backref='user', lazy=True,
    #                              foreign_keys='UserRole.user_id')

    uploaded_images = db.relationship('UploadedImage', backref='user', lazy=True,
                                      foreign_keys='UploadedImage.user_id')

    kyc_applications = db.relationship('KycApplication', backref='user', lazy=True,
                                      foreign_keys='KycApplication.user_id')

    devices          = db.relationship('DeviceInfo', backref='user', lazy=True)

    referrals        = db.relationship('Referral', backref='referring_user', lazy=True)

    transfer_card    = db.relationship('TransferCard', backref='user', lazy=True, uselist=False)

    credit_sends = db.relationship('CreditTransfer', backref='sender_user',
                                   lazy='dynamic', foreign_keys='CreditTransfer.sender_user_id')

    credit_receives = db.relationship('CreditTransfer', backref='recipient_user',
                                      lazy='dynamic', foreign_keys='CreditTransfer.recipient_user_id')

    ip_addresses     = db.relationship('IpAddress', backref='user', lazy=True)

    feedback            = db.relationship('Feedback', backref='user',
                                          lazy='dynamic', foreign_keys='Feedback.user_id')

    @hybrid_property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, phone):
        self._phone = proccess_phone_number(phone)

    @hybrid_property
    def public_serial_number(self):
        return self._public_serial_number

    @public_serial_number.setter
    def public_serial_number(self, public_serial_number):
        self._public_serial_number = public_serial_number

        try:
            transfer_card = get_transfer_card(public_serial_number)

            if transfer_card.user_id is None and transfer_card.nfc_serial_number is not None:
                # Card hasn't been used before, and has a nfc number attached
                self.nfc_serial_number = transfer_card.nfc_serial_number
                self.transfer_card = transfer_card

        except NoTransferCardError:
            pass

    @hybrid_property
    def tfa_url(self):

        if not self._TFA_secret:
            self.set_TFA_secret()
            db.session.commit()

        secret_key = self.get_TFA_secret()
        return pyotp.totp.TOTP(secret_key).provisioning_uri(
            self.email,
            issuer_name='Sempo: {}'.format(current_app.config.get('DEPLOYMENT_NAME'))
        )

    @hybrid_property
    def location(self):
        return self._location

    @location.setter
    def location(self, location):

        self._location = location

        if location is not None and location is not '':

            if self.id is None:
                raise AttributeError('User ID not set')

            try:
                task = {'user_id': self.id, 'address': location}
                geolocate_task = celery_app.signature('worker.celery_tasks.geolocate_address',
                                                      args=(task,))

                geolocate_task.delay()
            except Exception as e:
                print(e)
                sentry.captureException()
                pass

    @hybrid_property
    def roles(self):
        if self._held_roles is None:
            return {}
        return self._held_roles

    def set_held_role(self, role: str, tier: Union[str, None]):
        if role not in ACCESS_ROLES:
            raise RoleNotFoundException("Role '{}' not valid".format(role))
        allowed_tiers = ACCESS_ROLES[role]
        if tier is not None and tier not in allowed_tiers:
             raise TierNotFoundException("Tier {} not recognised for role {}".format(tier, role))

        if self._held_roles is None:
            self._held_roles = {}
        if tier is None:
            self._held_roles.pop(role, None)
        else:
            self._held_roles[role] = tier

    @hybrid_property
    def has_admin_role(self):
        return auth.AccessControl.has_any_tier(self.roles, 'ADMIN')

    @has_admin_role.expression
    def has_admin_role(cls):
        return cls._held_roles.has_key('ADMIN')

    @hybrid_property
    def has_vendor_role(self):
        return auth.AccessControl.has_any_tier(self.roles, 'VENDOR')

    @has_vendor_role.expression
    def has_vendor_role(cls):
        return cls._held_roles.has_key('VENDOR')

    @hybrid_property
    def has_beneficiary_role(self):
        return auth.AccessControl.has_any_tier(self.roles, 'BENEFICIARY')

    @has_beneficiary_role.expression
    def has_beneficiary_role(cls):
        return cls._held_roles.has_key('BENEFICIARY')

    @hybrid_property
    def admin_tier(self):
        return self._held_roles.get('ADMIN', None)

    @hybrid_property
    def vendor_tier(self):
        return self._held_roles.get('VENDOR', None)


    # These two are here to interface with the mobile API
    @hybrid_property
    def is_vendor(self):
        return auth.AccessControl.has_sufficient_tier(self.roles, 'VENDOR', 'vendor')

    @hybrid_property
    def is_supervendor(self):
        return auth.AccessControl.has_sufficient_tier(self.roles, 'VENDOR', 'supervendor')

    @hybrid_property
    def organisation_ids(self):
        return [organisation.id for organisation in self.organisations]

    @property
    def transfer_account(self):
        active_organisation = self.get_active_organisation()
        if active_organisation:
            return active_organisation.org_level_transfer_account

        # TODO: This should have a better concept of a default
        if len(self.transfer_accounts) == 1:
            return self.transfer_accounts[0]
        return None

    def get_active_organisation(self, fallback=None):
        if len(self.organisations) == 0:
            return fallback

        if len(self.organisations) > 1:
            return self.default_organisation

        return self.organisations[0]

    def update_last_seen_ts(self):
        cur_time = datetime.datetime.utcnow()
        if self._last_seen:
            if cur_time - self._last_seen >= datetime.timedelta(minutes=1):  # default to 1 minute intervals
                self._last_seen = cur_time
        else:
            self._last_seen = cur_time


    def hash_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def encode_TFA_token(self, valid_days = 1):
        """
        Generates the Auth Token for TFA
        :return: string
        """
        try:

            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=valid_days, seconds=30),
                'iat': datetime.datetime.utcnow(),
                'id': self.id
            }

            return jwt.encode(
                payload,
                current_app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        except Exception as e:
            return e

    def encode_auth_token(self):
        """
        Generates the Auth Token
        :return: string
        """
        try:

            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7, seconds=0),
                'iat': datetime.datetime.utcnow(),
                'id': self.id,
                'roles': self.roles
            }

            return jwt.encode(
                payload,
                current_app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token, token_type='Auth'):
        """
        Validates the auth token
        :param auth_token:
        :return: integer|string
        """
        try:
            payload = jwt.decode(auth_token, current_app.config.get('SECRET_KEY'), algorithms='HS256')
            is_blacklisted_token = BlacklistToken.check_blacklist(auth_token)
            if is_blacklisted_token:
                return 'Token blacklisted. Please log in again.'
            else:
                return payload

        except jwt.ExpiredSignatureError:
            return '{} Token Signature expired.'.format(token_type)
        except jwt.InvalidTokenError:
            return 'Invalid {} Token.'.format(token_type)

    def encode_single_use_JWS(self, token_type):

        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expires_in=current_app.config['TOKEN_EXPIRATION'])

        return s.dumps({'id': self.id, 'type': token_type}).decode("utf-8")

    @classmethod
    def decode_single_use_JWS(cls, token, required_type):

        try:
            s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])

            data = s.loads(token.encode("utf-8"))

            user_id = data.get('id')

            token_type = data.get('type')

            if token_type != required_type:
                return {'success': False, 'message': 'Wrong token type (needed %s)' % required_type}

            if not user_id:
                return {'success': False, 'message': 'No User ID provided'}

            user = cls.query.filter_by(id=user_id).execution_options(show_all=True).first()

            if not user:
                return {'success': False, 'message': 'User not found'}

            return {'success': True, 'user': user}

        except BadSignature:

            return {'success': False, 'message': 'Token signature not valid'}

        except SignatureExpired:

            return {'success': False, 'message': 'Token has expired'}

        except Exception as e:

            return {'success': False, 'message': e}

    def create_admin_auth(self, email, password, tier='view'):
        self.email = email
        self.hash_password(password)
        self.set_held_role('ADMIN', tier)

    def is_TFA_required(self):
        for tier in current_app.config['TFA_REQUIRED_ROLES']:
            if auth.AccessControl.has_exact_role(self.roles, 'ADMIN', tier):
                return True
        else:
            return False

    def is_TFA_secret_set(self):
        return bool(self._TFA_secret)

    def set_TFA_secret(self):
        secret = pyotp.random_base32()
        self._TFA_secret = encrypt_string(secret)

    def get_TFA_secret(self):
        return decrypt_string(self._TFA_secret)

    def validate_OTP(self, input_otp):
        try:
            p = int(input_otp)
        except ValueError:
            return False
        else:
            secret = self.get_TFA_secret()
            server_otp = pyotp.TOTP(secret)
            ret = server_otp.verify(p, valid_window=100)
            return ret

    def set_one_time_code(self, supplied_one_time_code):
        if supplied_one_time_code is None:
            self.one_time_code = str(random.randint(0, 9999)).zfill(4)
        else:
            self.one_time_code = supplied_one_time_code

    def set_pin(self, supplied_pin=None, is_activated=False):

        self.is_activated = is_activated

        if not is_activated:
            # Use a one time code, either generated or supplied. PIN will be set to random number for now
            self.set_one_time_code(supplied_one_time_code=supplied_pin)

            pin = str(random.randint(0, 9999)).zfill(4)
        else:
            pin = supplied_pin

        self.hash_password(pin)


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.secret = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    def __repr__(self):
        if self.has_admin_role:
            return '<Admin {} {}>'.format(self.id, self.email)
        elif self.has_vendor_role:
            return '<Vendor {} {}>'.format(self.id, self.phone)
        else:
            return '<User {} {}>'.format(self.id, self.phone)

class ChatbotState(ModelBase):
    __tablename__ = 'chatbot_state'

    transfer_initialised = db.Column(db.Boolean, default=False)
    target_user_id = db.Column(db.Integer, default=None)
    transfer_amount = db.Column(db.Integer, default=0)
    prev_pin_failures = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    provider_message_id = db.Column(db.String())

    user = db.relationship('User', backref='chatbot_state', lazy=True, uselist=False)


class DeviceInfo(ModelBase):
    __tablename__ = 'device_info'

    serial_number   = db.Column(db.String)
    unique_id       = db.Column(db.String)
    brand           = db.Column(db.String)
    model           = db.Column(db.String)

    height          = db.Column(db.Integer)
    width           = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))

class Token(ModelBase):
    __tablename__ = 'token'

    address = db.Column(db.String, index=True, unique=True, nullable=False)
    name    = db.Column(db.String)
    symbol  = db.Column(db.String)
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


class TransferAccount(OneOrgBase, ModelBase):
    __tablename__ = 'transfer_account'

    name            = db.Column(db.String())
    balance         = db.Column(db.BigInteger, default=0)
    blockchain_address = db.Column(db.String())

    is_approved     = db.Column(db.Boolean, default=False)

    # These are different from the permissions on the user:
    # is_vendor determines whether the account is allowed to have cash out operations etc
    # is_beneficiary determines whether the account is included in disbursement lists etc
    is_vendor       = db.Column(db.Boolean, default=False)

    is_beneficiary = db.Column(db.Boolean, default=False)

    payable_period_type   = db.Column(db.String(), default='week')
    payable_period_length = db.Column(db.Integer, default=2)
    payable_epoch         = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    token_id        = db.Column(db.Integer, db.ForeignKey(Token.id))

    transfer_card    = db.relationship('TransferCard', backref='transfer_account', lazy=True, uselist=False)

    # users               = db.relationship('User', backref='transfer_account', lazy=True)
    users = db.relationship(
        "User",
        secondary=user_transfer_account_association_table,
        back_populates="transfer_accounts")

    # owning_organisation_id = db.Column(db.Integer, db.ForeignKey(Organisation.id))

    # owning_organisation = db.relationship("Organsisation", backref='org_level_transfer_account',
    #                                       lazy='dynamic', foreign_keys=Organisation.org_level_transfer_account_id)

    # blockchain_address = db.relationship('BlockchainAddress', backref='transfer_account', lazy=True, uselist=False)

    credit_sends       = db.relationship('CreditTransfer', backref='sender_transfer_account',
                                         lazy='dynamic', foreign_keys='CreditTransfer.sender_transfer_account_id')

    credit_receives    = db.relationship('CreditTransfer', backref='recipient_transfer_account',
                                         lazy='dynamic', foreign_keys='CreditTransfer.recipient_transfer_account_id')

    spend_approvals_given = db.relationship('SpendApproval', backref='giving_transfer_account',
                                            lazy='dynamic', foreign_keys='SpendApproval.giving_transfer_account_id')

    def get_or_create_system_transfer_approval(self):

        organisation_blockchain_address = self.organisation.system_blockchain_address

        approval = self.get_approval(organisation_blockchain_address)

        if not approval:
            approval = self.give_approval_to_address(organisation_blockchain_address)

        return approval

    def give_approval_to_address(self, address_getting_approved):
        approval = SpendApproval(transfer_account_giving_approval=self,
                                 address_getting_approved=address_getting_approved)
        return approval

    def get_approval(self, receiving_address):
        for approval in self.spend_approvals_given:
            if approval.receiving_address == receiving_address:
                return approval
        return None

    @hybrid_property
    def total_sent(self):
        return int(
            db.session.query(func.sum(CreditTransfer.transfer_amount).label('total')).execution_options(show_all=True)
            .filter(CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE)
            .filter(CreditTransfer.sender_transfer_account_id == self.id).first().total or 0
        )

    @hybrid_property
    def total_received(self):
        return int(
            db.session.query(func.sum(CreditTransfer.transfer_amount).label('total')).execution_options(show_all=True)
            .filter(CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE)
            .filter(CreditTransfer.recipient_transfer_account_id == self.id).first().total or 0
        )

    # @hybrid_property
    # def balance(self):
    #     return self.total_received - self.total_sent

    @hybrid_property
    def primary_user(self):
        users = User.query.execution_options(show_all=True)\
            .filter(User.transfer_accounts.any(TransferAccount.id.in_([self.id]))).all()
        if len(users) == 0:
            # This only happens when we've unbound a user from a transfer account by manually editing the db
            return None

        return sorted(users, key=lambda user: user.created)[0]

    @hybrid_property
    def primary_user_id(self):
        return self.primary_user.id

    @hybrid_property
    def master_wallet_approval_status(self):

        if not current_app.config['USING_EXTERNAL_ERC20']:
            return 'NOT_REQUIRED'

        if not self.blockchain_address.encoded_private_key:
            return 'NOT_REQUIRED'

        base_query = (
            BlockchainTransaction.query
            .filter(BlockchainTransaction.transaction_type == 'master wallet approval')
            .filter(BlockchainTransaction.credit_transfer.has(recipient_transfer_account_id=self.id))
        )

        successful_transactions = base_query.filter(BlockchainTransaction.status == 'SUCCESS').all()

        if len(successful_transactions) > 0:
            return 'APPROVED'

        requested_transactions = base_query.filter(BlockchainTransaction.status == 'PENDING').all()

        if len(requested_transactions) > 0:
            return 'REQUESTED'

        failed_transactions = base_query.filter(BlockchainTransaction.status == 'FAILED').all()

        if len(failed_transactions) > 0:
            return 'FAILED'

        return 'NO_REQUEST'

    def approve(self):

        if not self.is_approved:
            self.is_approved = True

            if self.is_beneficiary:
                disbursement = self.make_initial_disbursement()
                return disbursement

    def make_initial_disbursement(self, initial_balance=None):

        if not initial_balance:
            initial_balance = current_app.config['STARTING_BALANCE']

        disbursement = make_disbursement_transfer(initial_balance, self)

        return disbursement

    def initialise_withdrawal(self, withdrawal_amount):

        withdrawal = make_withdrawal_transfer(withdrawal_amount,
                                              send_account=self,
                                              automatically_resolve_complete=False)
        return withdrawal

    def __init__(self, blockchain_address=None, organisation=None):
        #
        # blockchain_address_obj = BlockchainAddress(type="TRANSFER_ACCOUNT", blockchain_address=blockchain_address)
        # db.session.add(blockchain_address_obj)

        self.blockchain_address = blockchain_address or create_blockchain_wallet()

        if organisation:
            self.organisation = organisation
            self.token = organisation.token

class BlockchainAddress(OneOrgBase, ModelBase):
    __tablename__ = 'blockchain_address'

    address             = db.Column(db.String())
    encoded_private_key = db.Column(db.String())

    # Either "MASTER", "TRANSFER_ACCOUNT" or "EXTERNAL"
    type = db.Column(db.String())

    transfer_account_id = db.Column(db.Integer, db.ForeignKey(TransferAccount.id))

    signed_transactions = db.relationship('BlockchainTransaction',
                                          backref='signing_blockchain_address',
                                          lazy='dynamic',
                                          foreign_keys='BlockchainTransaction.signing_blockchain_address_id')

    credit_sends = db.relationship('CreditTransfer', backref='sender_blockchain_address',
                                   lazy='dynamic', foreign_keys='CreditTransfer.sender_blockchain_address_id')

    credit_receives = db.relationship('CreditTransfer', backref='recipient_blockchain_address',
                                      lazy='dynamic', foreign_keys='CreditTransfer.recipient_blockchain_address_id')

    @hybrid_property
    def decrypted_private_key(self):

        fernet_encryption_key = base64.b64encode(keccak(text=current_app.config['SECRET_KEY']))
        cipher_suite = Fernet(fernet_encryption_key)

        return cipher_suite.decrypt(self.encoded_private_key.encode('utf-8')).decode('utf-8')

    def encrypt_private_key(self, unencoded_private_key):

        fernet_encryption_key = base64.b64encode(keccak(text=current_app.config['SECRET_KEY']))
        cipher_suite = Fernet(fernet_encryption_key)

        return cipher_suite.encrypt(unencoded_private_key.encode('utf-8')).decode('utf-8')

    def calculate_address(self, private_key):
        self.address = hex_private_key_to_address(private_key)

    def allowed_types(self):
        return ALLOWED_BLOCKCHAIN_ADDRESS_TYPES

    def __init__(self, type, blockchain_address=None):

        if type not in self.allowed_types():
            raise Exception("type {} not one of {}".format(type, self.allowed_types()))

        self.type = type

        if blockchain_address:
            self.address = blockchain_address

        if self.type == "TRANSFER_ACCOUNT" and not blockchain_address:

            hex_private_key = Web3.toHex(keccak(os.urandom(4096)))

            self.encoded_private_key = self.encrypt_private_key(hex_private_key)

            self.calculate_address(hex_private_key)

class SpendApproval(ModelBase):
    __tablename__ = 'spend_approval'

    eth_send_task_id = db.Column(db.Integer)
    approval_task_id = db.Column(db.Integer)
    receiving_address = db.Column(db.String)

    token_id                      = db.Column(db.Integer, db.ForeignKey(Token.id))
    giving_transfer_account_id    = db.Column(db.Integer, db.ForeignKey(TransferAccount.id))

    def __init__(self, transfer_account_giving_approval, address_getting_approved):

        self.giving_transfer_account = transfer_account_giving_approval

        self.token = transfer_account_giving_approval.token

        self.receiving_address = address_getting_approved

        eth_send_task_id = send_eth(signing_address=address_getting_approved,
                                    recipient_address=transfer_account_giving_approval.blockchain_address,
                                    amount=0.00184196 * 10**18)

        approval_task_id = make_approval(signing_address=transfer_account_giving_approval.blockchain_address,
                                         token=self.token,
                                         spender=address_getting_approved,
                                         amount=1000000,
                                         dependent_on_tasks=[eth_send_task_id])

        self.eth_send_task_id = eth_send_task_id
        self.approval_task_id = approval_task_id



class CreditTransfer(ManyOrgBase, ModelBase):
    __tablename__ = 'credit_transfer'

    uuid            = db.Column(db.String, unique=True)

    resolved_date   = db.Column(db.DateTime)
    transfer_amount = db.Column(db.Integer)

    transfer_type   = db.Column(db.Enum(TransferTypeEnum))
    transfer_status = db.Column(db.Enum(TransferStatusEnum), default=TransferStatusEnum.PENDING)
    transfer_mode   = db.Column(db.Enum(TransferModeEnum))
    transfer_use    = db.Column(JSON)

    resolution_message = db.Column(db.String())

    blockchain_task_id = db.Column(db.Integer)

    token_id        = db.Column(db.Integer, db.ForeignKey(Token.id))

    sender_transfer_account_id       = db.Column(db.Integer, db.ForeignKey(TransferAccount.id))
    recipient_transfer_account_id    = db.Column(db.Integer, db.ForeignKey(TransferAccount.id))

    sender_blockchain_address_id    = db.Column(db.Integer, db.ForeignKey("blockchain_address.id"))
    recipient_blockchain_address_id = db.Column(db.Integer, db.ForeignKey("blockchain_address.id"))

    sender_user_id    = db.Column(db.Integer, db.ForeignKey(User.id))
    recipient_user_id = db.Column(db.Integer, db.ForeignKey(User.id))

    blockchain_transactions = db.relationship('BlockchainTransaction', backref='credit_transfer', lazy=True)

    attached_images = db.relationship('UploadedImage', backref='credit_transfer', lazy=True)

    @hybrid_property
    def blockchain_status(self):
        if self.blockchain_task_id:
            task = get_blockchain_task(self.blockchain_task_id)

            return task.get('status', 'ERROR')
        else:
            return 'UNKNOWN'

        # if len(self.uncompleted_blockchain_tasks) == 0:
        #     return 'COMPLETE'
        #
        # if len(self.pending_blockchain_tasks) > 0:
        #     return 'PENDING'
        #
        # if len(self.failed_blockchain_tasks) > 0:
        #     return 'ERROR'
        #
        # return 'UNKNOWN'


    @hybrid_property
    def blockchain_status_breakdown(self):

        required_task_dict = {x: {'status': 'UNKNOWN', 'hash': None} for x in self._get_required_blockchain_tasks()}

        for transaction in self.blockchain_transactions:
            status_hierarchy = ['UNKNOWN', 'FAILED', 'PENDING', 'SUCCESS']
            task_type = transaction.transaction_type

            current_status = required_task_dict.get(task_type).get('status')
            proposed_new_status = transaction.status

            try:
                if current_status and status_hierarchy.index(proposed_new_status) > status_hierarchy.index(current_status):
                    required_task_dict[task_type]['status'] = proposed_new_status
                    required_task_dict[task_type]['hash'] = transaction.hash
            except ValueError:
                pass

        return required_task_dict

    @hybrid_property
    def pending_blockchain_tasks(self):
        return self._find_blockchain_tasks_with_status_of('PENDING')

    @hybrid_property
    def failed_blockchain_tasks(self):
        return self._find_blockchain_tasks_with_status_of('FAILED')

    @hybrid_property
    def uncompleted_blockchain_tasks(self):
        required_task_set = set(self._get_required_blockchain_tasks())
        completed_task_set = self._find_blockchain_tasks_with_status_of('SUCCESS')
        return required_task_set - completed_task_set

    def _get_required_blockchain_tasks(self):
        if self.transfer_type == TransferTypeEnum.DISBURSEMENT and not current_app.config['IS_USING_BITCOIN']:

            if current_app.config['USING_EXTERNAL_ERC20']:
                master_wallet_approval_status = self.recipient_transfer_account.master_wallet_approval_status

                if (master_wallet_approval_status in ['APPROVED', 'NOT_REQUIRED']
                    and float(current_app.config['FORCE_ETH_DISBURSEMENT_AMOUNT']) <= 0):

                    required_tasks = ['disbursement']

                elif master_wallet_approval_status in ['APPROVED', 'NOT_REQUIRED']:

                    required_tasks = ['disbursement', 'ether load']

                else:
                    required_tasks = ['disbursement', 'ether load', 'master wallet approval']

            else:
                required_tasks = ['initial credit mint']

        else:
            required_tasks = ['transfer']

        return required_tasks

    def _find_blockchain_tasks_with_status_of(self, required_status):
        if required_status not in ['PENDING', 'SUCCESS', 'FAILED']:
            raise Exception('required_status must be one of PENDING, SUCCESS or FAILED')

        completed_task_set = set()
        for transaction in self.blockchain_transactions:
            if transaction.status == required_status:
                completed_task_set.add(transaction.transaction_type)
        return completed_task_set

    def send_blockchain_payload_to_worker(self, is_retry=False):

        sender_approval = self.sender_transfer_account.get_or_create_system_transfer_approval()

        recipient_approval = self.recipient_transfer_account.get_or_create_system_transfer_approval()

        self.blockchain_task_id = make_token_transfer(
            signing_address=self.sender_transfer_account.organisation.system_blockchain_address,
            token=self.token,
            from_address=self.sender_transfer_account.blockchain_address,
            to_address=self.recipient_transfer_account.blockchain_address,
            amount=self.transfer_amount,
            dependent_on_tasks=[
                sender_approval.eth_send_task_id, sender_approval.approval_task_id,
                recipient_approval.eth_send_task_id, recipient_approval.approval_task_id
            ]
        )

    def resolve_as_completed(self, existing_blockchain_txn=None):
        self.resolved_date = datetime.datetime.utcnow()
        self.transfer_status = TransferStatusEnum.COMPLETE

        self.sender_transfer_account.balance -= self.transfer_amount
        self.recipient_transfer_account.balance += self.transfer_amount

        if self.transfer_type == TransferTypeEnum.DISBURSEMENT:
            if self.recipient_user and self.recipient_user.transfer_card:
                self.recipient_user.transfer_card.update_transfer_card()

        if not existing_blockchain_txn:
            self.send_blockchain_payload_to_worker()

    def resolve_as_rejected(self, message=None):
        self.resolved_date = datetime.datetime.utcnow()
        self.transfer_status = TransferStatusEnum.REJECTED

        if message:
            self.resolution_message = message

    def check_sender_has_sufficient_balance(self):
        return self.sender_user and self.sender_transfer_account.balance - self.transfer_amount >= 0

    def check_sender_is_approved(self):
        return self.sender_user and self.sender_transfer_account.is_approved

    def check_recipient_is_approved(self):
        return self.recipient_user and self.recipient_transfer_account.is_approved

    def find_user_transfer_accounts_with_matching_token(self, user, token):
        matching_transfer_accounts = []
        for transfer_account in user.transfer_accounts:
            if transfer_account.token == token:
                matching_transfer_accounts.append(transfer_account)
        if len(matching_transfer_accounts) == 0:
            raise NoTransferAccountError("No transfer account for user {} and token".format(user, token))
        if len(matching_transfer_accounts) > 1:
            raise Exception(f"User has multiple transfer accounts for token {token}")

        return matching_transfer_accounts[0]

    def _select_transfer_account(self, supplied_transfer_account, user, token):
        if token is None:
            raise Exception("Token must be specified")
        if supplied_transfer_account:
            if user is not None and user not in supplied_transfer_account.users:
                raise UserNotFoundError(f'User {user} not found for transfer account {supplied_transfer_account}')
            return supplied_transfer_account

        return self.find_user_transfer_accounts_with_matching_token(user, token)

    def append_organisation_if_required(self, organisation):
        if organisation not in self.organisations:
            self.organisations.append(organisation)

    def __init__(self,
                 amount,
                 token=None,
                 sender_user=None,
                 recipient_user=None,
                 sender_transfer_account=None,
                 recipient_transfer_account=None,
                 transfer_type=None, uuid=None):

        self.transfer_amount = amount

        self.sender_user = sender_user
        self.recipient_user = recipient_user

        self.sender_transfer_account = sender_transfer_account or self._select_transfer_account(
            sender_transfer_account, sender_user, token)

        self.token = token or self.sender_transfer_account.token

        self.recipient_transfer_account = recipient_transfer_account or self._select_transfer_account(
            recipient_transfer_account, recipient_user, self.token)

        if self.sender_transfer_account.token != self.recipient_transfer_account.token:
            raise Exception("Tokens do not match")

        self.transfer_type = transfer_type

        if uuid is not None:
            self.uuid = uuid

        self.append_organisation_if_required(self.recipient_transfer_account.organisation)
        self.append_organisation_if_required(self.sender_transfer_account.organisation)


class BlockchainTransaction(ModelBase):
    __tablename__ = 'blockchain_transaction'

    status = db.Column(db.String)  # PENDING, SUCCESS, FAILED
    message = db.Column(db.String)
    block = db.Column(db.Integer)
    submitted_date = db.Column(db.DateTime)
    added_date = db.Column(db.DateTime)
    hash = db.Column(db.String)
    nonce = db.Column(db.Integer)
    transaction_type = db.Column(db.String)

    is_bitcoin = db.Column(db.Boolean)

    # Output spent txn for bitcoin
    has_output_txn = db.Column(db.Boolean, default=False)

    credit_transfer_id = db.Column(db.Integer, db.ForeignKey(CreditTransfer.id))

    signing_blockchain_address_id = db.Column(db.Integer, db.ForeignKey('blockchain_address.id'))


class Feedback(ModelBase):
    __tablename__ = 'feedback'

    question                = db.Column(db.String)
    rating                  = db.Column(db.Float)
    additional_information  = db.Column(db.String)

    user_id                 = db.Column(db.Integer, db.ForeignKey(User.id))


class Referral(ModelBase):
    __tablename__ = 'referral'

    first_name              = db.Column(db.String)
    last_name               = db.Column(db.String)
    reason                  = db.Column(db.String)

    _phone                  = db.Column(db.String())

    @hybrid_property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, phone):
        self._phone = proccess_phone_number(phone)

    referring_user_id     = db.Column(db.Integer, db.ForeignKey(User.id))

class TargetingSurvey(ModelBase):
    __tablename__ = 'targeting_survey'

    number_people_household             = db.Column(db.Integer)
    number_below_adult_age_household    = db.Column(db.Integer)
    number_people_women_household       = db.Column(db.Integer)
    number_people_men_household         = db.Column(db.Integer)
    number_people_work_household        = db.Column(db.Integer)
    disabilities_household              = db.Column(db.String)
    long_term_illnesses_household       = db.Column(db.String)

    user = db.relationship('User', backref='targeting_survey', lazy=True, uselist=False)


class CurrencyConversion(ModelBase):
    __tablename__ = 'currency_conversion'

    code = db.Column(db.String)
    rate = db.Column(db.Float)

class Settings(ModelBase):
    __tablename__ = 'settings'

    name        = db.Column(db.String)
    type        = db.Column(db.String)
    value       = db.Column(JSON)

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

    email               = db.Column(db.String)

    tier                = db.Column(db.String, default='view')
    referral_code       = db.Column(db.String)

    allow_partial_match = db.Column(db.Boolean, default=False)
    used                = db.Column(db.Boolean, default=False)



    def __init__(self, **kwargs):
        super(EmailWhitelist, self).__init__(**kwargs)
        self.referral_code = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

class TransferCard(ModelBase):
    __tablename__ = 'transfer_card'

    public_serial_number = db.Column(db.String)
    nfc_serial_number    = db.Column(db.String)
    PIN                  = db.Column(db.String)

    _amount_loaded          = db.Column(db.Integer)
    amount_loaded_signature = db.Column(db.String)

    user_id    = db.Column(db.Integer, db.ForeignKey(User.id))

    transfer_account_id    = db.Column(db.Integer, db.ForeignKey(TransferAccount.id))


    @hybrid_property
    def amount_loaded(self):
        return self._phone

    @amount_loaded.setter
    def amount_loaded(self, amount):
        self._amount_loaded = amount
        message = '{}{}{}'.format(self.nfc_serial_number, amount, self.transfer_account.token.symbol)
        self.amount_loaded_signature = current_app.config['ECDSA_SIGNING_KEY'].sign(message.encode()).hex()

    def update_transfer_card(self):
        disbursements = (CreditTransfer.query
                         .execution_options(show_all=True)
                         .filter_by(recipient_user_id=self.user_id)
                         .filter_by(transfer_type=TransferTypeEnum.DISBURSEMENT)
                         .filter_by(transfer_status=TransferStatusEnum.COMPLETE)
                         .all())

        total_disbursed = 0

        for disbursement in disbursements:
            total_disbursed += disbursement.transfer_amount

        self.amount_loaded = total_disbursed

class SavedFilter(ModelBase):
    __tablename__ = 'saved_filter'

    name          = db.Column(db.String)
    filter        = db.Column(JSON)


class KycApplication(ModelBase):
    __tablename__       = 'kyc_application'

    # compliance
    trulioo_id          = db.Column(db.String)
    namescan_scan_id    = db.Column(db.String)

    # Wyre SRN
    wyre_id             = db.Column(db.String)

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

    uploaded_documents = db.relationship('UploadedDocument', backref='kyc_application', lazy=True,
                                         foreign_keys='UploadedDocument.kyc_application_id')

    bank_accounts        = db.relationship('BankAccount', backref='kyc_application', lazy=True,
                                           foreign_keys='BankAccount.kyc_application_id')

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))

    def __init__(self, type, **kwargs):
        super(KycApplication, self).__init__(**kwargs)
        if type not in ALLOWED_KYC_TYPES:
            raise TypeNotFoundException('Type {} not found'.format(type))

        self.type = type
        self.kyc_attempts = 1

        if type == 'INDIVIDUAL':
            self.kyc_status = 'PENDING'


class BankAccount(ModelBase):
    __tablename__       = 'bank_account'

    # Wyre SRN
    wyre_id = db.Column(db.String)

    kyc_application_id = db.Column(db.Integer, db.ForeignKey('kyc_application.id'))

    bank_country        = db.Column(db.String)
    routing_number      = db.Column(db.String)
    account_number      = db.Column(db.String)
    currency            = db.Column(db.String)


class UploadedImage(ModelBase):
    __tablename__ = 'uploaded_image'

    filename = db.Column(db.String)
    image_type = db.Column(db.String)
    credit_transfer_id = db.Column(db.Integer, db.ForeignKey(CreditTransfer.id))
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))

    @hybrid_property
    def image_url(self):
        return get_file_url(self.filename)


class UploadedDocument(ModelBase):
    __tablename__               = 'uploaded_document'

    kyc_application_id = db.Column(db.Integer, db.ForeignKey('kyc_application.id'))

    filename                    = db.Column(db.String)
    file_type                   = db.Column(db.String)
    user_filename               = db.Column(db.String)
    reference                   = db.Column(db.String)

    @hybrid_property
    def file_url(self):
        return get_file_url(self.filename)


class TransferUsage(ModelBase):
    __tablename__               = 'transfer_usage'

    name                        = db.Column(db.String)
    is_cashout                  = db.Column(db.Boolean)
    _icon                       = db.Column(db.String)
    priority                    = db.Column(db.Integer)
    translations                = db.Column(JSON)

    @hybrid_property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, icon):
        if icon not in MATERIAL_COMMUNITY_ICONS:
            raise IconNotSupportedException('Icon {} not supported or found'.format(icon))
        self._icon = icon


class CustomAttribute(ModelBase):
    __tablename__               = 'custom_attribute'

    name                        = db.Column(db.String)


class IpAddress(ModelBase):
    __tablename__               = 'ip_address'

    _ip                         = db.Column(INET)
    country                     = db.Column(db.String)

    user_id                     = db.Column(db.Integer, db.ForeignKey('user.id'))

    @staticmethod
    def check_user_ips(user, ip_address):
        # check whether ip address is saved for a given user
        res = IpAddress.query.filter_by(ip=ip_address, user_id=user.id).first()
        if res:
            return True
        else:
            return False

    @hybrid_property
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, ip):

        self._ip = ip

        if ip is not None:

            try:
                task = {'ip_address_id': self.id, 'ip': ip}
                ip_location_task = celery_app.signature('worker.celery_tasks.ip_location', args=(task,))

                ip_location_task.delay()
            except Exception as e:
                print(e)
                sentry.captureException()
                pass


class FiatRamp(ModelBase):
    """
    FiatRamp model handles multiple on and off ramps (exchanging fiat for crypto)

    credit_transfer_id: references addition or withdrawal of user funds in the exchange process
    """

    __tablename__               = 'fiat_ramp'

    _payment_method             = db.Column(db.String)
    payment_status              = db.Column(db.Enum(FiatRampStatusEnum), default=FiatRampStatusEnum.PENDING)

    credit_transfer_id = db.Column(db.Integer, db.ForeignKey(CreditTransfer.id))

    payment_metadata            = db.Column(JSON)

    @hybrid_property
    def payment_method(self):
        return self._payment_method

    @payment_method.setter
    def payment_method(self, payment_method):
        if payment_method not in PAYMENT_METHODS:
            raise PaymentMethodException('Payment method {} not found'.format(payment_method))

        self._payment_method = payment_method
