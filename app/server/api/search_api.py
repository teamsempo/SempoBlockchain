from flask import Blueprint, request, g
import datetime

from flask.views import MethodView
from sqlalchemy.sql.expression import func
from sqlalchemy import desc, asc

from server.utils.auth import requires_auth
from server.utils.transfer_filter import process_transfer_filters
from server.utils.search import generate_search_query
from server.schemas import transfer_accounts_schema
from server.models.utils import paginate_query
from server.utils.access_control import AccessControl

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
        sort_by_arg = request.args.get('sort_by') or 'rank'

        final_query = generate_search_query(search_string, filters, order, sort_by_arg)
        transfer_accounts, total_items, total_pages, _ = paginate_query(final_query, ignore_last_fetched=True)
        accounts = [resultTuple[0] for resultTuple in transfer_accounts]
        if AccessControl.has_sufficient_tier(g.user.roles, 'ADMIN', 'admin'):
            result = transfer_accounts_schema.dump(accounts)
        elif AccessControl.has_any_tier(g.user.roles, 'ADMIN'):
            result = view_transfer_accounts_schema.dump(accounts)

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
