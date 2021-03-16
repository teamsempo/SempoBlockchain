from flask import current_app
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import ARRAY
import pendulum
import secrets
from decimal import Decimal

from server import db, bt
from server.models.utils import ModelBase, organisation_association_table
import server.models.transfer_account
from server.utils.misc import encrypt_string, decrypt_string
from server.utils.access_control import AccessControl
import server.models.transfer_account
from server.utils.misc import encrypt_string
from server.constants import ISO_COUNTRIES, ASSIGNABLE_TIERS


class Organisation(ModelBase):
    """
    Establishes organisation object that resources can be associated with.
    """
    __tablename__       = 'organisation'

    is_master           = db.Column(db.Boolean, default=False, index=True)

    name                = db.Column(db.String)

    external_auth_username = db.Column(db.String)

    valid_roles = db.Column(ARRAY(db.String, dimensions=1))

    _external_auth_password = db.Column(db.String)

    default_lat = db.Column(db.Float())
    default_lng = db.Column(db.Float())
    
    # 0 means don't shard, units are kilometers
    card_shard_distance = db.Column(db.Integer, default=0) 

    _timezone = db.Column(db.String, default='UTC')
    _country_code = db.Column(db.String, nullable=False)
    _default_disbursement_wei = db.Column(db.Numeric(27), default=0)
    require_transfer_card = db.Column(db.Boolean, default=False)

    # TODO: Create a mixin so that both user and organisation can use the same definition here
    # This is the blockchain address used for transfer accounts, unless overridden
    primary_blockchain_address = db.Column(db.String)

    # This is the 'behind the scenes' blockchain address used for paying gas fees
    system_blockchain_address = db.Column(db.String)

    auto_approve_externally_created_users = db.Column(db.Boolean, default=False)

    users               = db.relationship(
        "User",
        secondary=organisation_association_table,
        back_populates="organisations")

    token_id            = db.Column(db.Integer, db.ForeignKey('token.id'))

    org_level_transfer_account_id = db.Column(db.Integer,
                                                db.ForeignKey('transfer_account.id',
                                                name="fk_org_level_account"))

    _minimum_vendor_payout_withdrawal_wei = db.Column(db.Numeric(27), default=0)

    # We use this weird join pattern because SQLAlchemy
    # doesn't play nice when doing multiple joins of the same table over different declerative bases
    org_level_transfer_account = db.relationship(
        "TransferAccount",
        post_update=True,
        primaryjoin="Organisation.org_level_transfer_account_id==TransferAccount.id",
        uselist=False)

    @hybrid_property
    def timezone(self):
        return self._timezone

    @timezone.setter
    def timezone(self, val):
        # Make the timezone case insensitive
        lower_zones = dict(zip([tz.lower() for tz in pendulum.timezones], pendulum.timezones))
        if val is not None and val.lower() not in lower_zones:
            raise Exception(f"{val} is not a valid timezone")
        self._timezone = lower_zones[val.lower()]

    @hybrid_property
    def country_code(self):
        return self._country_code

    @hybrid_property
    def country(self):
        if self._country_code not in ISO_COUNTRIES:
            raise Exception(f"{self._country_code} is not a valid timezone")
        return ISO_COUNTRIES[self._country_code]

    @country_code.setter
    def country_code(self, val):
        if val is not None:
            val = val.upper()
            if len(val) != 2:
                # will try handle 'AD: Andorra'
                val = val.split(':')[0]
            if val not in ISO_COUNTRIES:
                raise Exception(f"{val} is not a valid country code")
        self._country_code = val

    @property
    def default_disbursement(self):
        return Decimal((self._default_disbursement_wei or 0) / int(1e16))

    @default_disbursement.setter
    def default_disbursement(self, val):
        if val is not None:
            self._default_disbursement_wei = int(val) * int(1e16)

    @property
    def minimum_vendor_payout_withdrawal(self):
        return Decimal((self._minimum_vendor_payout_withdrawal_wei or 0) / int(1e16))

    @minimum_vendor_payout_withdrawal.setter
    def minimum_vendor_payout_withdrawal(self, val):
        if val is not None:
            self._minimum_vendor_payout_withdrawal_wei = int(val) * int(1e16)

    # TODO: This is a hack to get around the fact that org level TAs don't always show up. Super not ideal
    @property
    def queried_org_level_transfer_account(self):
        if self.org_level_transfer_account_id:
            return server.models.transfer_account.TransferAccount\
                .query.execution_options(show_all=True).get(self.org_level_transfer_account_id)
        return None

    @hybrid_property
    def external_auth_password(self):
        return decrypt_string(self._external_auth_password)

    @external_auth_password.setter
    def external_auth_password(self, value):
        self._external_auth_password = encrypt_string(value)

    credit_transfers    = db.relationship("CreditTransfer",
                                          secondary=organisation_association_table,
                                          back_populates="organisations")

    transfer_accounts   = db.relationship('TransferAccount',
                                          backref='organisation',
                                          lazy=True, foreign_keys='TransferAccount.organisation_id')

    blockchain_addresses = db.relationship('BlockchainAddress', backref='organisation',
                                           lazy=True, foreign_keys='BlockchainAddress.organisation_id')

    email_whitelists    = db.relationship('EmailWhitelist', backref='organisation',
                                          lazy=True, foreign_keys='EmailWhitelist.organisation_id')

    kyc_applications = db.relationship('KycApplication', backref='organisation',
                                       lazy=True, foreign_keys='KycApplication.organisation_id')

    attribute_maps = db.relationship('AttributeMap', backref='organisation',
                                       lazy=True, foreign_keys='AttributeMap.organisation_id')

    custom_welcome_message_key = db.Column(db.String)

    @staticmethod
    def master_organisation() -> "Organisation":
        return Organisation.query.filter_by(is_master=True).first()

    def _setup_org_transfer_account(self):
        transfer_account = server.models.transfer_account.TransferAccount(
            bound_entity=self,
            is_approved=True
        )
        db.session.add(transfer_account)
        self.org_level_transfer_account = transfer_account

        # Back setup for delayed organisation transfer account instantiation
        for user in self.users:
            if AccessControl.has_any_tier(user.roles, 'ADMIN'):
                user.transfer_accounts.append(self.org_level_transfer_account)

    def bind_token(self, token):
        self.token = token
        self._setup_org_transfer_account()

    def __init__(self, token=None, is_master=False, valid_roles=None, timezone=None, **kwargs):
        super(Organisation, self).__init__(**kwargs)
        self.timezone = timezone if timezone else 'UTC'
        chain = self.token.chain if self.token else current_app.config['DEFAULT_CHAIN']
        self.external_auth_username = 'admin_'+ self.name.lower().replace(' ', '_')
        self.external_auth_password = secrets.token_hex(16)
        self.valid_roles = valid_roles or list(ASSIGNABLE_TIERS.keys())
        if is_master:
            if Organisation.query.filter_by(is_master=True).first():
                raise Exception("A master organisation already exists")
            self.is_master = True
            self.system_blockchain_address = bt.create_blockchain_wallet(
                private_key=current_app.config['CHAINS'][chain]['MASTER_WALLET_PRIVATE_KEY'],
                wei_target_balance=0,
                wei_topup_threshold=0,
            )

            self.primary_blockchain_address = self.system_blockchain_address or bt.create_blockchain_wallet()

        else:
            self.is_master = False

            self.system_blockchain_address = bt.create_blockchain_wallet(
                wei_target_balance=current_app.config['CHAINS'][chain]['SYSTEM_WALLET_TARGET_BALANCE'],
                wei_topup_threshold=current_app.config['CHAINS'][chain]['SYSTEM_WALLET_TOPUP_THRESHOLD'],
            )

            self.primary_blockchain_address = bt.create_blockchain_wallet()

        if token:
            self.bind_token(token)
