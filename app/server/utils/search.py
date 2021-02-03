from functools import reduce

from flask import request
from sqlalchemy import func, asc, desc

from server import db
from server.models.transfer_account import TransferAccount
from server.models.user import User
from server.utils.metrics.filters import apply_filters
from server.utils.transfer_filter import process_transfer_filters


class SearchableColumn:
    def __init__(self, name, column, rank=1):
        self.name = name
        self.column = column
        self.rank = rank

    def get_similarity_query(self, query):
        return (func.coalesce(func.similarity(self.column, query), 0).label('first_name_rank') * self.rank)


def generate_user_search_filter_query():
    # HANDLE PARAM : search_stirng - Any search string. An empty string (or None) will just return everything!
    search_string = request.args.get('search_string') or ''
    # HANDLE PARAM : params - Standard filter object. Exact same as the ones Metrics uses!
    encoded_filters = request.args.get('params')
    filters = process_transfer_filters(encoded_filters)
    # HANDLE PARAM : order
    # Valid orders types are: `ASC` and `DESC`
    # Default: DESC
    order_arg = request.args.get('order') or 'DESC'
    if order_arg.upper() not in ['ASC', 'DESC']:
        return {'message': 'Invalid order value \'{}\'. Please use \'ASC\' or \'DESC\''.format(order_arg)}
    order = asc if order_arg.upper() == 'ASC' else desc
    # HANDLE PARAM: sort_by
    # Valid orders types are: first_name, last_name, email, date_account_created, rank, balance, status
    # Default: rank
    sort_types_to_database_types = {
        'first_name': User.first_name,
        'last_name': User.last_name,
        'email': User.email,
        'date_account_created': User.created,
        'rank': 'rank',
        'balance': TransferAccount._balance_wei,
        'status': TransferAccount.is_approved,
    }
    sort_by_arg = request.args.get('sort_by') or 'rank'
    if sort_by_arg not in sort_types_to_database_types:
        return {
            'message': f'Invalid sort_by value {sort_by_arg}. Please use one of the following: {sort_types_to_database_types.keys()}' \
            }

    # To add new searchable column, simply add a new SearchableColumn object!
    # And don't forget to add a trigram index on that column too-- see migration 33df5e72fca4 for reference
    user_search_columns = [
        SearchableColumn('first_name', User.first_name, rank=1.5),
        SearchableColumn('last_name', User.last_name, rank=1.5),
        SearchableColumn('phone', User.phone, rank=2),
        SearchableColumn('public_serial_number', User.public_serial_number, rank=2),
        SearchableColumn('location', User.location, rank=1),
        SearchableColumn('primary_blockchain_address', User.primary_blockchain_address, rank=2),
    ]

    sum_search = reduce(lambda x, y: x + y, [sc.get_similarity_query(search_string) for sc in user_search_columns])
    sort_by = sum_search if sort_by_arg == 'rank' else sort_types_to_database_types[sort_by_arg]
    # If there's no search string, the process is the same, just sort by account creation date
    sort_by = sort_types_to_database_types[
        'date_account_created'] if sort_by == 'rank' and not search_string else sort_by

    final_query = db.session.query(TransferAccount, User) \
        .outerjoin(TransferAccount, User.default_transfer_account_id == TransferAccount.id) \
        .with_entities(TransferAccount) \
        .order_by(order(sort_by))

    # If there is a search string, we only want to return ranked results!
    final_query = final_query.filter(sum_search != 0) if search_string else final_query

    final_query = apply_filters(final_query, filters, User)

    return final_query