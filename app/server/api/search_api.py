from flask import Blueprint

import datetime

from flask.views import MethodView

from server.utils.auth import requires_auth
from server.utils.search import generate_user_search_filter_query
from server.schemas import transfer_accounts_schema
from server.models.utils import paginate_query
from server.models.transfer_account import TransferAccount

search_blueprint = Blueprint('search', __name__)


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

        final_query = generate_user_search_filter_query().filter(TransferAccount.is_ghost != True)

        transfer_accounts, total_items, total_pages, _ = paginate_query(final_query, ignore_last_fetched=True)
        result = transfer_accounts_schema.dump(transfer_accounts)

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
