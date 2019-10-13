from sqlalchemy import event, inspect
from sqlalchemy.orm.query import Query
from flask import g, current_app

from server import db
from server.exceptions import (
    OrganisationNotProvidedException
)
from server.utils.blockchain_tasks import (
    create_blockchain_wallet
)
from server.models.utils import ModelBase, OneOrgBase, ManyOrgBase, organisation_association_table

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
