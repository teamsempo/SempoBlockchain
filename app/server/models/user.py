import json
from typing import Union
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy import text
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature, SignatureExpired
import pyotp
from flask import current_app, g
import datetime
import bcrypt
import jwt
import random
import string

from server import db, sentry, celery_app, bt
from server.utils.misc import encrypt_string, decrypt_string
from server.utils.access_control import AccessControl
from server.utils.phone import proccess_phone_number

from server.utils.transfer_account import (
    find_transfer_accounts_with_matching_token
)

import server.models.transfer_account
from server.models.utils import ModelBase, ManyOrgBase, user_transfer_account_association_table
from server.models.organisation import Organisation
from server.models.blacklist_token import BlacklistToken
from server.models.transfer_card import TransferCard
from server.models.transfer_usage import TransferUsage
from server.exceptions import (
    RoleNotFoundException,
    TierNotFoundException,
    NoTransferCardError
)
from server.constants import (
    ACCESS_ROLES
)


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

    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    preferred_language = db.Column(db.String())

    primary_blockchain_address = db.Column(db.String())

    _last_seen = db.Column(db.DateTime)

    email = db.Column(db.String())
    _phone = db.Column(db.String(), unique=True)
    _public_serial_number = db.Column(db.String())
    nfc_serial_number = db.Column(db.String())

    password_hash = db.Column(db.String(128))
    one_time_code = db.Column(db.String)
    secret = db.Column(db.String())
    _TFA_secret = db.Column(db.String(128))
    TFA_enabled = db.Column(db.Boolean, default=False)
    pin_hash = db.Column(db.String())

    failed_pin_attempts = db.Column(db.Integer, default=0)

    default_currency = db.Column(db.String())

    _location = db.Column(db.String())
    lat = db.Column(db.Float())
    lng = db.Column(db.Float())

    _held_roles = db.Column(JSONB)

    is_activated = db.Column(db.Boolean, default=False)
    is_disabled = db.Column(db.Boolean, default=False)
    is_phone_verified = db.Column(db.Boolean, default=False)
    is_self_sign_up = db.Column(db.Boolean, default=True)

    password_reset_tokens = db.Column(JSONB, default=[])
    pin_reset_tokens = db.Column(JSONB, default=[])

    terms_accepted = db.Column(db.Boolean, default=True)

    matched_profile_pictures = db.Column(JSON)

    cashout_authorised = db.Column(db.Boolean, default=False)

    business_usage_id = db.Column(db.Integer, db.ForeignKey(TransferUsage.id))

    transfer_accounts = db.relationship(
        "TransferAccount",
        secondary=user_transfer_account_association_table,
        back_populates="users")

    default_transfer_account_id = db.Column(db.Integer, db.ForeignKey('transfer_account.id'))

    default_transfer_account = db.relationship('TransferAccount',
                                           primaryjoin='TransferAccount.id == User.default_transfer_account_id',
                                           lazy=True,
                                           uselist=False)

    default_organisation_id = db.Column(
        db.Integer, db.ForeignKey('organisation.id'))

    default_organisation = db.relationship('Organisation',
                                           primaryjoin=Organisation.id == default_organisation_id,
                                           lazy=True,
                                           uselist=False)

    # roles = db.relationship('UserRole', backref='user', lazy=True,
    #                              foreign_keys='UserRole.user_id')

    uploaded_images = db.relationship('UploadedResource', backref='user', lazy=True,
                                      foreign_keys='UploadedResource.user_id')

    kyc_applications = db.relationship('KycApplication', backref='user', lazy=True,
                                       foreign_keys='KycApplication.user_id')

    devices = db.relationship('DeviceInfo', backref='user', lazy=True)

    referrals = db.relationship(
        'Referral', backref='referring_user', lazy=True)

    transfer_card = db.relationship(
        'TransferCard', backref='user', lazy=True, uselist=False)

    credit_sends = db.relationship('CreditTransfer', backref='sender_user',
                                   lazy='dynamic', foreign_keys='CreditTransfer.sender_user_id')

    credit_receives = db.relationship('CreditTransfer', backref='recipient_user',
                                      lazy='dynamic', foreign_keys='CreditTransfer.recipient_user_id')

    ip_addresses = db.relationship('IpAddress', backref='user', lazy=True)

    feedback = db.relationship('Feedback', backref='user',
                               lazy='dynamic', foreign_keys='Feedback.user_id')

    custom_attributes = db.relationship("CustomAttributeUserStorage", backref='user',
                                        lazy='dynamic', foreign_keys='CustomAttributeUserStorage.user_id')

    exchanges = db.relationship("Exchange", backref="user")

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
            transfer_card = TransferCard.get_transfer_card(
                public_serial_number)

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
            issuer_name='Sempo: {}'.format(
                current_app.config.get('DEPLOYMENT_NAME'))
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
            raise TierNotFoundException(
                "Tier {} not recognised for role {}".format(tier, role))

        if self._held_roles is None:
            self._held_roles = {}
        if tier is None:
            self._held_roles.pop(role, None)
        else:
            self._held_roles[role] = tier

    @hybrid_property
    def has_admin_role(self):
        return AccessControl.has_any_tier(self.roles, 'ADMIN')

    @has_admin_role.expression
    def has_admin_role(cls):
        return cls._held_roles.has_key('ADMIN')

    @hybrid_property
    def has_vendor_role(self):
        return AccessControl.has_any_tier(self.roles, 'VENDOR')

    @has_vendor_role.expression
    def has_vendor_role(cls):
        return cls._held_roles.has_key('VENDOR')

    @hybrid_property
    def has_beneficiary_role(self):
        return AccessControl.has_any_tier(self.roles, 'BENEFICIARY')

    @has_beneficiary_role.expression
    def has_beneficiary_role(cls):
        return cls._held_roles.has_key('BENEFICIARY')

    @hybrid_property
    def has_token_agent_role(self):
        return AccessControl.has_any_tier(self.roles, 'TOKEN_AGENT')

    @hybrid_property
    def has_group_account_role(self):
        return AccessControl.has_any_tier(self.roles, 'GROUP_ACCOUNT')

    @hybrid_property
    def admin_tier(self):
        return self._held_roles.get('ADMIN', None)

    @hybrid_property
    def vendor_tier(self):
        return self._held_roles.get('VENDOR', None)

    # These two are here to interface with the mobile API
    @hybrid_property
    def is_vendor(self):
        return AccessControl.has_sufficient_tier(self.roles, 'VENDOR', 'vendor')

    @hybrid_property
    def is_supervendor(self):
        return AccessControl.has_sufficient_tier(self.roles, 'VENDOR', 'supervendor')

    @hybrid_property
    def organisation_ids(self):
        return [organisation.id for organisation in self.organisations]

    @property
    def transfer_account(self):
        active_organisation = getattr(g, "active_organisation", None) or self.fallback_active_organisation()
        if active_organisation:
            return active_organisation.org_level_transfer_account

        # TODO: This should have a better concept of a default
        if len(self.transfer_accounts) == 1:
            return self.transfer_accounts[0]
        return None

    def get_transfer_account_for_token(self, token):
        return find_transfer_accounts_with_matching_token(self, token)

    def fallback_active_organisation(self):
        if len(self.organisations) == 0:
            return None

        if len(self.organisations) > 1:
            return self.default_organisation

        return self.organisations[0]

    def update_last_seen_ts(self):
        cur_time = datetime.datetime.utcnow()
        if self._last_seen:
            # default to 1 minute intervals
            if cur_time - self._last_seen >= datetime.timedelta(minutes=1):
                self._last_seen = cur_time
        else:
            self._last_seen = cur_time

    @staticmethod
    def salt_hash_secret(password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def check_salt_hashed_secret(password, hashed_password):
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    def hash_password(self, password):
        self.password_hash = self.salt_hash_secret(password)

    def verify_password(self, password):
        return self.check_salt_hashed_secret(password, self.password_hash)

    def hash_pin(self, pin):
        self.pin_hash = self.salt_hash_secret(pin)

    def verify_pin(self, pin):
        return self.check_salt_hashed_secret(pin, self.pin_hash)

    def encode_TFA_token(self, valid_days=1):
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
            payload = jwt.decode(auth_token, current_app.config.get(
                'SECRET_KEY'), algorithms='HS256')
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

        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'],
                                            expires_in=current_app.config['TOKEN_EXPIRATION'])

        return s.dumps({'id': self.id, 'type': token_type}).decode("utf-8")

    @classmethod
    def decode_single_use_JWS(cls, token, required_type):

        try:
            s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'])

            data = s.loads(token.encode("utf-8"))

            user_id = data.get('id')

            token_type = data.get('type')

            if token_type != required_type:
                return {'success': False, 'message': 'Wrong token type (needed %s)' % required_type}

            if not user_id:
                return {'success': False, 'message': 'No User ID provided'}

            user = cls.query.filter_by(
                id=user_id).execution_options(show_all=True).first()

            if not user:
                return {'success': False, 'message': 'User not found'}

            return {'success': True, 'user': user}

        except BadSignature:

            return {'success': False, 'message': 'Token signature not valid'}

        except SignatureExpired:

            return {'success': False, 'message': 'Token has expired'}

        except Exception as e:

            return {'success': False, 'message': e}

    def save_password_reset_token(self, password_reset_token):
        # make a "clone" of the existing token list
        self.clear_expired_password_reset_tokens()
        current_password_reset_tokens = self.password_reset_tokens[:]
        current_password_reset_tokens.append(password_reset_token)
        # set db value
        self.password_reset_tokens = current_password_reset_tokens

    def save_pin_reset_token(self, pin_reset_token):
        self.clear_expired_password_reset_tokens()

        current_pin_reset_tokens = self.pin_reset_tokens[:]
        current_pin_reset_tokens.append(pin_reset_token)

        self.pin_reset_tokens = current_pin_reset_tokens

    def check_reset_token_already_used(self, password_reset_token):
        self.clear_expired_password_reset_tokens()
        is_valid = password_reset_token in self.password_reset_tokens
        return is_valid

    def delete_password_reset_tokens(self):
        self.password_reset_tokens = []

    def delete_pin_reset_tokens(self):
        self.pin_reset_tokens = []

    def clear_expired_reset_tokens(self, token_list):
        if token_list is None:
            token_list = []

        valid_tokens = []
        for token in token_list:
            validity_check = self.decode_single_use_JWS(token, 'R')
            if validity_check['success']:
                valid_tokens.append(token)
        return valid_tokens

    def clear_expired_password_reset_tokens(self):
        tokens = self.clear_expired_reset_tokens(self.password_reset_tokens)
        self.password_reset_tokens = tokens

    def clear_expired_pin_reset_tokens(self):
        tokens = self.clear_expired_reset_tokens(self.pin_reset_tokens)
        self.pin_reset_tokens = tokens

    def create_admin_auth(self, email, password, tier='view', organisation=None):
        self.email = email
        self.hash_password(password)
        self.set_held_role('ADMIN', tier)

        if organisation:
            self.add_user_to_organisation(organisation, is_admin=True)

    def add_user_to_organisation(self, organisation: Organisation, is_admin=False):
        self.organisations.append(organisation)
        self.default_organisation = organisation

        if is_admin:
            if organisation.org_level_transfer_account is None:
                organisation.org_level_transfer_account = (
                    db.session.query(server.models.transfer_account.TransferAccount)
                    .execution_options(show_all=True)
                    .get(organisation.org_level_transfer_account_id))

            self.transfer_accounts.append(organisation.org_level_transfer_account)

    def is_TFA_required(self):
        for tier in current_app.config['TFA_REQUIRED_ROLES']:
            if AccessControl.has_exact_role(self.roles, 'ADMIN', tier):
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
        secret = self.get_TFA_secret()
        server_otp = pyotp.TOTP(secret)
        ret = server_otp.verify(input_otp, valid_window=2)
        return ret

    def set_one_time_code(self, supplied_one_time_code):
        if supplied_one_time_code is None:
            self.one_time_code = str(random.randint(0, 9999)).zfill(4)
        else:
            self.one_time_code = supplied_one_time_code

    # pin as used in mobile. is set to password. we should probably change this to be same as ussd pin
    def set_pin(self, supplied_pin=None, is_activated=False):
        self.is_activated = is_activated

        if not is_activated:
            # Use a one time code, either generated or supplied. PIN will be set to random number for now
            self.set_one_time_code(supplied_one_time_code=supplied_pin)

            pin = str(random.randint(0, 9999)).zfill(4)
        else:
            pin = supplied_pin

        self.hash_password(pin)

    def has_valid_pin(self):
        # not in the process of resetting pin and has a pin
        self.clear_expired_pin_reset_tokens()
        not_resetting = len(self.pin_reset_tokens) == 0

        return self.pin_hash is not None and not_resetting

    def user_details(self):
        # should drop the country code from phone number?
        return "{} {} {}".format(self.first_name, self.last_name, self.phone)

    def get_most_relevant_transfer_usages(self):
        '''Finds the transfer usage/business categories there are most relevant for the user
        based on the last number of send and completed credit transfers supplemented with the
        defaul business categories
        :return: list of most relevant transfer usage objects for the usage
        """
        '''

        sql = text('''
            SELECT *, COUNT(*) FROM
                (SELECT c.transfer_use::text FROM credit_transfer c
                WHERE c.sender_user_id = {} AND c.transfer_status = 'COMPLETE'
                ORDER BY c.updated DESC
                LIMIT 20)
            C GROUP BY transfer_use ORDER BY count DESC
        '''.format(self.id))
        result = db.session.execute(sql)
        most_common_uses = {}
        for row in result:
            if row[0] is not None:
                for use in json.loads(row[0]):
                    most_common_uses[use] = row[1]

        return most_common_uses

    def get_reserve_token(self):
        # reserve token is master token for now
        return Organisation.master_organisation().token

    def __init__(self, blockchain_address=None, **kwargs):
        super(User, self).__init__(**kwargs)

        self.secret = ''.join(random.choices(
            string.ascii_letters + string.digits, k=16))

        self.primary_blockchain_address = blockchain_address or bt.create_blockchain_wallet()

    def __repr__(self):
        if self.has_admin_role:
            return '<Admin {} {}>'.format(self.id, self.email)
        elif self.has_vendor_role:
            return '<Vendor {} {}>'.format(self.id, self.phone)
        else:
            return '<User {} {}>'.format(self.id, self.phone)
