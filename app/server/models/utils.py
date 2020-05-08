from contextlib import contextmanager
from flask import g, request
import datetime
from dateutil import parser

from sqlalchemy import event, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Query
from sqlalchemy import or_

import server
from server import db, bt
from server.exceptions import OrganisationNotProvidedException, ResourceAlreadyDeletedError

@contextmanager
def ephemeral_alchemy_object(mod: db.Model, *args, **kwargs):
    # weird SQLAlchemy behaviour cause object  to be persisted under some circumstances, even if they're not committed
    # See: https://hades.github.io/2013/06/sqlalchemy-adds-objects-collections-automatically/
    # Use this to make sure an object definitely doesn't hang round

    instance = mod(*args, **kwargs)
    yield instance

    for f in [db.session.expunge, db.session.delete]:
        # Can't delete transient objects, so we expunge them first instead
        try:
            f(instance)
        except:
            # We don't care about no exceptions, we just want the object GONE!!!
            pass


def get_authorising_user_id():
    if hasattr(g, 'user'):
        return g.user.id
    elif hasattr(g, 'authorising_user_id'):
        return g.authorising_user_id
    else:
        return None


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

    updated_after = request.args.get('updated_after')
    page = request.args.get('page')
    per_page = request.args.get('per_page')

    if updated_after:
        parsed_time = parser.isoparse(updated_after)
        query = query.filter(queried_object.updated > parsed_time)

    if order_override:
        query = query.order_by(order_override)
    elif queried_object:
        query = query.order_by(queried_object.id.desc())

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


@contextmanager
def no_expire():
    s = db.session()
    s.expire_on_commit = False
    yield
    s.expire_on_commit = True


@event.listens_for(Query, "before_compile", retval=True)
def before_compile(query):
    """A query compilation rule that will add limiting criteria for every
    subclass of OrgBase"""
    show_deleted = query._execution_options.get("show_deleted", False)
    show_all = getattr(g, "show_all", False) or query._execution_options.get("show_all", False)

    if show_all and show_deleted:
        return query

    for ent in query.column_descriptions:
        entity = ent['entity']
        if entity is None:
            continue
        insp = inspect(ent['entity'])
        mapper = getattr(insp, 'mapper', None)

        if mapper:
            # if subclass SoftDelete exists and not show_deleted, return non-deleted items, else show deleted
            if issubclass(mapper.class_, SoftDelete) and not show_deleted:
                query = query.enable_assertions(False).filter(ent['entity'].deleted == None)

            if show_all and not show_deleted:
                return query

            # if the subclass OrgBase exists, then filter by organisations - else, return default query
            if issubclass(mapper.class_, ManyOrgBase) or issubclass(mapper.class_, OneOrgBase):

                try:
                    # member_organisations = getattr(g, "member_organisations", [])
                    active_organisation = getattr(g, "active_organisation", None)
                    active_organisation_id = getattr(active_organisation, "id", None)
                    member_organisation_ids = [active_organisation_id] if active_organisation_id else []

                    if issubclass(mapper.class_, ManyOrgBase):
                        # filters many-to-many
                        query = query.enable_assertions(False).filter(or_(
                            ent['entity'].organisations.any(
                                server.models.organisation.Organisation.id.in_(member_organisation_ids)),
                            ent['entity'].is_public == True,
                        ))
                    else:
                        query = query.enable_assertions(False).filter(or_(
                            ent['entity'].organisation_id == active_organisation_id,
                            ent['entity'].is_public == True,
                        ))

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


user_transfer_account_association_table = db.Table(
    'user_transfer_account_association_table',
    db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), index=True),
    db.Column('transfer_account_id', db.Integer, db.ForeignKey('transfer_account.id'), index=True)
)

organisation_association_table = db.Table(
    'organisation_association_table',
    db.Model.metadata,
    db.Column('organisation_id', db.Integer, db.ForeignKey('organisation.id'), index=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), index=True),
    db.Column('transfer_account_id', db.Integer, db.ForeignKey('transfer_account.id'), index=True),
    db.Column('credit_transfer_id', db.Integer, db.ForeignKey('credit_transfer.id'), index=True),
)

exchange_contract_token_association_table = db.Table(
    'exchange_contract_token_association_table',
    db.Model.metadata,
    db.Column('exchange_contract_id', db.Integer, db.ForeignKey("exchange_contract.id")),
    db.Column('token_id', db.Integer, db.ForeignKey('token.id'))
)


class ModelBase(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    authorising_user_id = db.Column(db.Integer, default=get_authorising_user_id)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class BlockchainTaskableBase(ModelBase):
    __abstract__ = True

    blockchain_task_uuid = db.Column(db.String)

    @hybrid_property
    def blockchain_status(self):
        if self.blockchain_task_uuid:
            task = bt.get_blockchain_task(self.blockchain_task_uuid)

            return task.get('status', 'ERROR')
        else:
            return 'UNKNOWN'


class SoftDelete(object):
    """
    Mixing that adds standard soft deletion functionality to object
    """

    _deleted = db.Column(db.DateTime)

    @hybrid_property
    def deleted(self):
        return self._deleted

    @deleted.setter
    def deleted(self, deleted):
        if self._deleted:
            raise ResourceAlreadyDeletedError('Resource Already Deleted')
        self._deleted = deleted


class OneOrgBase(object):
    """
    Mixin that automatically associates object(s) to organisation(s) many-to-one.

    Forces all database queries on associated objects to provide an organisation ID or specify show_all=True flag
    """

    is_public = db.Column(db.Boolean, default=False)

    @declared_attr
    def organisation_id(cls):
        return db.Column('organisation_id', db.ForeignKey('organisation.id'))


class ManyOrgBase(object):
    """
    Mixin that automatically associates object(s) to organisation(s) many-to-many.

    Forces all database queries on associated objects to provide an organisation ID or specify show_all=True flag
    """

    is_public = db.Column(db.Boolean, default=False)

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
