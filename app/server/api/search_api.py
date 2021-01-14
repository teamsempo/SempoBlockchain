from flask import Blueprint, request
import datetime

from flask.views import MethodView
from sqlalchemy.sql.expression import func
from sqlalchemy import desc, asc

from server import db
from server.utils.auth import requires_auth
from server.utils.transfer_filter import process_transfer_filters
from server.schemas import transfer_accounts_schema
from server.models.utils import paginate_query
from server.utils.metrics.filters import apply_filters
from server.models.transfer_account import TransferAccount
from server.models.user import User
from functools import reduce

search_blueprint = Blueprint('search', __name__)


class SearchableColumn:
    def __init__(self, name, column, rank=1):
        self.name = name
        self.column = column
        self.rank = rank

    def get_similarity_query(self, query):
        return (func.coalesce(func.similarity(self.column, query), 0).label('first_name_rank') * self.rank)

class SearchAPI(MethodView):
    """
        This endpoint searches transfer accounts. It will check first name/last name/phone number/email address/public_serial_number/
        location/primary_blockchain_address
        Parameters:
            - search_string: Any string you want to search. When empty or not provided, all results will be returned. 
            - order: Which order to return results in (ASC or DESC)
            - sort_by: What to sort by.
        Return Value:
            Results object, similar to the existing transfer_accounts API return values
    """
    @requires_auth(allowed_roles={'ADMIN': 'any'})
    def get(self):
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
            return { 'message': 'Invalid order value \'{}\'. Please use \'ASC\' or \'DESC\''.format(order_arg)}
        order = asc if order_arg.upper()=='ASC' else desc
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
                'message': f'Invalid sort_by value {sort_by_arg}. Please use one of the following: {sort_types_to_database_types.keys()}'\
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

        sum_search = reduce(lambda x,y: x+y, [sc.get_similarity_query(search_string) for sc in user_search_columns])
        sort_by = sum_search if sort_by_arg == 'rank' else sort_types_to_database_types[sort_by_arg]
        # If there's no search string, the process is the same, just sort by account creation date
        sort_by = sort_types_to_database_types['date_account_created'] if sort_by == 'rank' and not search_string else sort_by

        final_query = db.session.query(TransferAccount, User, sum_search)\
            .with_entities(TransferAccount, sum_search)\
            .outerjoin(TransferAccount, User.default_transfer_account_id == TransferAccount.id)\
            .filter(TransferAccount.is_ghost != True)\
            .order_by(order(sort_by))
        # If there is a search string, we only want to return ranked results!
        final_query = final_query.filter(sum_search!=0) if search_string else final_query

        final_query = apply_filters(final_query, filters, User)
        transfer_accounts, total_items, total_pages, _ = paginate_query(final_query, ignore_last_fetched=True)
        result = transfer_accounts_schema.dump([resultTuple[0] for resultTuple in transfer_accounts])

        return {
            'message': 'Successfully Loaded.',
            'items': total_items,
            'pages': total_pages,
            'query_time': datetime.datetime.utcnow(),
            'data': { 'transfer_accounts': result.data }
        }

search_blueprint.add_url_rule(
    '/search/',
    view_func=SearchAPI.as_view('search_view'),
    methods=['GET']
)
