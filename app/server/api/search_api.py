from flask import Blueprint, request, make_response, jsonify
import datetime

from flask.views import MethodView
import re
import json
from sqlalchemy.sql.expression import func
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import aliased

from server import db, bt
from server.utils.auth import requires_auth
from server.utils.transfer_filter import process_transfer_filters

from server.schemas import transfer_accounts_schema, credit_transfers_schema
from server.models.utils import paginate_query
from server.utils.metrics.filters import apply_filters
from server.models.search import SearchView
from server.models.transfer_account import TransferAccount
from server.models.credit_transfer import CreditTransfer
from server.models.user import User

search_blueprint = Blueprint('search', __name__)


class SearchAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'any'})
    def get(self):
        """
        This endpoint searches transfer accounts and credit transfers. It will check first name/last name/phone number/email address
        Parameters:
            - search_string: Any string you want to search. When empty or not provided, all results will be returned. 
            - search_type: Valid inputs are transfer_accounts, and credit_transfers.
            - order: Which order to return results in (ASC or DESC)
            - sort_by: What to sort by. `rank` works for both, and sorts by search relevance.
                - Transfer Accounts can be sorted by: 'first_name', 'last_name', 'email', 'date_account_created', 'rank', 'balance', 'status'
                - Credit Transfers can be sorted by: 'sender_first_name', 'sender_last_name', 'sender_email', 'sender_date_account_created', 
                  'recipient_first_name', 'recipient_last_name', 'recipient_email', 'recipient_date_account_created', 'rank', 'amount', 
                  'transfer_type', 'approval', 'date_transaction_created'
        Return Value:
            Results object, similar to the existing transfer_accounts and credit_transfers API return values
        """
        # HANDLE PARAM : search_stirng
        search_string = request.args.get('search_string') or ''      

        # HANDLE PARAM : search_type
        # Valid search types are: `transfer_accounts` and `credit_transfers`
        # Default: transfer_accounts
        search_type = request.args.get('search_type') or 'transfer_accounts'
        if search_type not in ['transfer_accounts', 'credit_transfers']:
            response_object = {
                'message': 'Invalid search_type \'{}\'. Please use type \'transfer_accounts\' or \'credit_transfers\''.format(search_type),
            }
            return make_response(jsonify(response_object)), 400

        # HANDLE PARAM : sort_by
        # Valid params differ depending on sort_by. See: sort_by
        # Default: rank
        
        # Aliases used for joining the separate sender and recipient objects to transfers
        sender = aliased(User)
        recipient = aliased(User)
        # Build order by object
        sort_types_to_database_types = {'first_name': User.first_name,
                                        'last_name': User.last_name,
                                        'email': User.email,
                                        'date_account_created': User.created,
                                        'rank': 'rank',
                                        'balance': TransferAccount._balance_wei,
                                        'status': TransferAccount.is_approved,
                                        'amount': CreditTransfer.transfer_amount,
                                        'transfer_type': CreditTransfer.transfer_type,
                                        'approval': CreditTransfer.transfer_status,
                                        'date_transaction_created': CreditTransfer.resolved_date,
                                        'sender_first_name': sender.first_name,
                                        'sender_last_name': sender.last_name,
                                        'sender_email': sender.email,
                                        'sender_date_account_created': recipient.created,
                                        'recipient_first_name': recipient.first_name,
                                        'recipient_last_name': recipient.last_name,
                                        'recipient_email': recipient.email,
                                        'recipient_date_account_created': recipient.created
                                        }

        # These lists are to validate the user input-- not using sort_types_to_database_types since credit_transfers and transfer_accounts have unique options 
        user_sorting_options = ['first_name', 'last_name', 'email', 'date_account_created']
        sender_sorting_options = list(map(lambda s: 'sender_'+s, user_sorting_options)) # sender_first_name, sender_last_name, etc...
        recipient_sorting_options = list(map(lambda s: 'recipient_'+s, user_sorting_options)) # recipient_first_name, recipient_last_name, etc...
        sorting_options = { 'transfer_accounts': [*user_sorting_options, 'rank', 'balance', 'status'] ,
                            'credit_transfers':[*sender_sorting_options, *recipient_sorting_options, 'rank', 'amount', 'transfer_type', 'approval', 'date_transaction_created'] }
        sort_by_arg = request.args.get('sort_by') or 'rank'
        if sort_by_arg not in sorting_options[search_type]:
            response_object = {
                # Example output:
                # "Invalid sort_by value 'pizza'. Please use one of the following: 'first_name', 'last_name', 'email', 'rank', 'balance', 'status', 'date_account_created'"
                'message': 'Invalid sort_by value \'{}\'. Please use one of the following: {}'\
                    .format(sort_by_arg, ', '.join('\'{}\''.format(a) for a in sorting_options[search_type])),
            }
            return make_response(jsonify(response_object)), 400
        sort_by = sort_types_to_database_types[sort_by_arg]

        encoded_filters = request.args.get('params')
        filters = process_transfer_filters(encoded_filters)
        
        # HANDLE PARAM : order
        # Valid orders types are: `ASC` and `DESC`
        # Default: DESC
        order_arg = request.args.get('order') or 'DESC'
        if order_arg not in ['ASC', 'DESC']:
            response_object = {
                'message': 'Invalid order value \'{}\'. Please use \'ASC\' or \'DESC\''.format(order_arg),
            }
            return make_response(jsonify(response_object)), 400
        order = desc
        if order_arg == 'ASC':
            order = asc

        # Note: Using tsquery wildcards here. Good docs of them here:
        # https://www.postgresql.org/docs/current/datatype-textsearch.html#DATATYPE-TSQUERY
        # 'Fran deRoo' -> 'Fran:* | deRoo:*'
        # Matches strings like "Francine deRoos"
        # Will also match "Michiel deRoos" because of the or clause, but this will be ranked lower
        search_string = re.sub('\s+',' ',search_string)
        search_terms = search_string.strip().split(' ')
        tsquery = ':* | '.join(search_terms)+':*'

        # Return everything if the search string is empty
        if search_string == '':
            if search_type == 'transfer_accounts':
                final_query = TransferAccount.query.filter(TransferAccount.is_ghost != True)\
                    .join(User, User.default_transfer_account_id == TransferAccount.id)
                final_query = apply_filters(final_query, filters, User)
                if sort_by_arg == 'rank':
                    # There's no search rank when there's no query string, so do chrono instead
                    final_query = final_query.order_by(order(User.created))                    
                else:
                    final_query = final_query.order_by(order(sort_by))

                transfer_accounts, total_items, total_pages, new_last_fetched = paginate_query(final_query)
                result = transfer_accounts_schema.dump(transfer_accounts)
                data = { 'transfer_accounts': result.data }
            else:
                final_query = CreditTransfer.query.filter()\
                    .outerjoin(sender, sender.default_transfer_account_id == CreditTransfer.sender_transfer_account_id)\
                    .outerjoin(recipient, recipient.default_transfer_account_id == CreditTransfer.recipient_transfer_account_id)
                if sort_by_arg == 'rank':
                    # There's no search rank when there's no query string, so do chrono instead
                    final_query = final_query.order_by(order(CreditTransfer.created))                    
                else:
                    final_query = final_query.order_by(order(sort_by))

                credit_transfers, total_items, total_pages, new_last_fetched = paginate_query(final_query)
                result = credit_transfers_schema.dump(credit_transfers)
                data = { 'credit_transfers': result.data }

        else:
            # First get users who match search string
            user_search_result = db.session.query(
                db.distinct(SearchView.id),
                SearchView,
                # This ugly (but functional) multi-tscolumn ranking is a modified from Ben Smithgall's blog post
                # https://www.codeforamerica.org/blog/2015/07/02/multi-table-full-text-search-with-postgres-flask-and-sqlalchemy/
                db.func.max(db.func.full_text.ts_rank(
                    db.func.setweight(db.func.coalesce(SearchView.tsv_email, ''), 'D')\
                        .concat(db.func.setweight(db.func.coalesce(SearchView.tsv_phone, ''), 'A'))\
                        .concat(db.func.setweight(db.func.coalesce(SearchView.tsv_first_name, ''), 'B'))\
                        .concat(db.func.setweight(db.func.coalesce(SearchView.tsv_last_name, ''), 'B'))\
                        .concat(db.func.setweight(db.func.coalesce(SearchView.tsv_public_serial_number, ''), 'A'))\
                        .concat(db.func.setweight(db.func.coalesce(SearchView.tsv_primary_blockchain_address, ''), 'A'))\
                        .concat(db.func.setweight(db.func.coalesce(SearchView.tsv_location, ''), 'C'))\
                        .concat(db.func.setweight(db.func.coalesce(SearchView.tsv_default_transfer_account_id, ''), 'A')),
                        db.func.to_tsquery(tsquery, postgresql_regconfig='english')))\
                .label('rank'))\
                .group_by(SearchView)\
                .subquery()

            # Then use those results to join aginst TransferAccount or CreditTransfer
            if search_type == 'transfer_accounts':
            # TransferAccount Search Logic
                final_query = db.session.query(TransferAccount)\
                    .join(user_search_result, user_search_result.c.default_transfer_account_id == TransferAccount.id)\
                    .join(User, user_search_result.c.default_transfer_account_id == User.default_transfer_account_id)\
                    .filter(user_search_result.c.rank > 0.0)\
                    .filter(TransferAccount.is_ghost != True)
                final_query = apply_filters(final_query, filters, User)

                if sort_by_arg == 'rank':
                    final_query = final_query.order_by(order(user_search_result.c.rank))
                else:
                    final_query = final_query.order_by(order(sort_by))

                transfer_accounts, total_items, total_pages, new_last_fetched = paginate_query(final_query)
                result = transfer_accounts_schema.dump(transfer_accounts)
                data = { 'transfer_accounts': result.data }
            # CreditTransfer Search Logic
            else:
                sender_search_result = aliased(user_search_result)
                recipient_search_result = aliased(user_search_result)
                # Join the search results objects to sort by rank, as well as aliased user objects (sender/recipient) for other sorting options
                final_query = db.session.query(CreditTransfer)\
                    .outerjoin(sender_search_result, 
                        sender_search_result.c.default_transfer_account_id == CreditTransfer.sender_transfer_account_id
                    )\
                    .outerjoin(recipient_search_result, 
                        recipient_search_result.c.default_transfer_account_id == CreditTransfer.recipient_transfer_account_id
                    )\
                    .outerjoin(sender, 
                        sender_search_result.c.default_transfer_account_id == sender.default_transfer_account_id
                    )\
                    .outerjoin(recipient, 
                        recipient_search_result.c.default_transfer_account_id == recipient.default_transfer_account_id
                    )\
                    .filter(or_(recipient_search_result.c.rank > 0.0, sender_search_result.c.rank > 0.0))

                if sort_by_arg == 'rank':
                    final_query = final_query.order_by(order(recipient_search_result.c.rank + sender_search_result.c.rank))
                else:
                    final_query = final_query.order_by(order(sort_by))
                credit_transfers, total_items, total_pages, new_last_fetched = paginate_query(final_query)
                result = credit_transfers_schema.dump(credit_transfers)
                data = { 'credit_transfers': result.data }

        response_object = {
            'message': 'Successfully Loaded.',
            'items': total_items,
            'pages': total_pages,
            'last_fetched': new_last_fetched,
            'query_time': str(datetime.datetime.utcnow()),
            'data': data
        }

        bytes_data = json.dumps(response_object)
        resp = make_response(bytes_data, 200)
        resp.mimetype = 'application/json'
        return resp

search_blueprint.add_url_rule(
    '/search/',
    view_func=SearchAPI.as_view('search_view'),
    methods=['GET']
)
