from contextlib import contextmanager
from sqlalchemy import event, inspect
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.query import Query
from flask import g, request, current_app
import datetime, random, string

from server.exceptions import (
    IconNotSupportedException,
    OrganisationNotProvidedException
)
from server.constants import (
    MATERIAL_COMMUNITY_ICONS
)
from server import db
from server.utils.blockchain_tasks import (
    create_blockchain_wallet,
    get_token_decimals
)
from server.models.utils import ModelBase, OneOrgBase, ManyOrgBase, organisation_association_table

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

# todo: see if we can dynamically generate org relationships from mapper args??
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

class ChatbotState(ModelBase):
    __tablename__ = 'chatbot_state'

    transfer_initialised = db.Column(db.Boolean, default=False)
    target_user_id = db.Column(db.Integer, default=None)
    transfer_amount = db.Column(db.Integer, default=0)
    prev_pin_failures = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    provider_message_id = db.Column(db.String())

    user = db.relationship('User', backref='chatbot_state', lazy=True, uselist=False)



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

class SavedFilter(ModelBase):
    __tablename__ = 'saved_filter'

    name          = db.Column(db.String)
    filter        = db.Column(JSON)

class BankAccount(ModelBase):
    __tablename__       = 'bank_account'

    # Wyre SRN
    wyre_id = db.Column(db.String)

    kyc_application_id = db.Column(db.Integer, db.ForeignKey('kyc_application.id'))

    bank_country        = db.Column(db.String)
    routing_number      = db.Column(db.String)
    account_number      = db.Column(db.String)
    currency            = db.Column(db.String)

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
            raise IconNotSupportedException('Icon {} not supported or found')
        self._icon = icon


class CustomAttribute(ModelBase):
    __tablename__               = 'custom_attribute'

    name                        = db.Column(db.String)


