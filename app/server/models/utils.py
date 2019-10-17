from contextlib import contextmanager

from flask import g, request
import datetime

from sqlalchemy import event, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Query

import server
from server import db
from server.exceptions import OrganisationNotProvidedException


def get_authorising_user_id():
    if hasattr(g,'user'):
        return g.user.id
    elif hasattr(g,'authorising_user_id'):
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
                            ent['entity'].organisations.any(server.models.organisation.Organisation.id.in_(member_organisations))
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


user_transfer_account_association_table = db.Table(
    'user_transfer_account_association_table',
    db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('transfer_account_id', db.Integer, db.ForeignKey('transfer_account.id'))
)

organisation_association_table = db.Table(
    'organisation_association_table',
    db.Model.metadata,
    db.Column('organisation_id', db.Integer, db.ForeignKey('organisation.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('transfer_account_id', db.Integer, db.ForeignKey('transfer_account.id')),
    db.Column('credit_transfer_id', db.Integer, db.ForeignKey('credit_transfer.id')),
)


class ModelBase(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    authorising_user_id = db.Column(db.Integer, default=get_authorising_user_id)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


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
