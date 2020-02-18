from flask import Blueprint, request, make_response, jsonify
import datetime
import orjson

from flask.views import MethodView
import re
import json
from sqlalchemy.sql.expression import func
from sqlalchemy import or_

from server import db, bt
from server.utils.auth import requires_auth
from server.models.utils import paginate_query
from server.schemas import transfer_accounts_schema, credit_transfers_schema
from server.models.search import SearchView
from server.models.transfer_account import TransferAccount
from server.models.credit_transfer import CreditTransfer

search_blueprint = Blueprint('search', __name__)


class SearchAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'any'})
    def get(self):
        """
        This endpoint searches transfer accounts and credit transfers. It will check first name/last name/phone number/email address
        Parameters:
            - search_string: Any string you want to search. When empty or not provided, all results will be returned. 
            - search_type: Valid inputs are transfer_accounts, and credit_transfers.
        Return Value:
            Results object, similar to the existing transfer_accounts and credit_transfers API return values
        """
        search_string = request.args.get('search_string') or ''

        # Valid search types are: `transfer_accounts` and `credit_transfers`
        search_type = request.args.get('search_type') or 'transfer_accounts'
        if search_type not in ['transfer_accounts', 'credit_transfers']:
            response_object = {
                'message': 'Invalid search_type \'{}\'. Please use type \'transfer_accounts\' or \'credit_transfers\''.format(search_type),
            }
            return make_response(jsonify(response_object)), 400

        # Note: Using tsquery wildcards here. Good docs of them here:
        # https://www.postgresql.org/docs/current/datatype-textsearch.html#DATATYPE-TSQUERY
        # 'Fran deRoo' -> 'Fran:* | deRoo:*'
        # Matches strings like "Francine deRoos"
        # Will also match "Michiel deRoos" because of the or clause, but this will be ranked lower
        search_terms = search_string.strip().split(' ')
        tsquery = ':* | '.join(search_terms)+':*'

        # Return everything if the search string is empty
        if search_string == '':
            if search_type == 'transfer_accounts':
                final_query = TransferAccount.query.filter(TransferAccount.is_ghost != True)\
                    .execution_options(show_all=True)
                transfer_accounts, total_items, total_pages = paginate_query(final_query, TransferAccount)
                result = transfer_accounts_schema.dump(transfer_accounts)
                data = { 'transfer_accounts': result.data }
            else:
                final_query = CreditTransfer.query.filter()\
                    .execution_options(show_all=True)
                credit_transfers, total_items, total_pages = paginate_query(final_query, CreditTransfer)
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
                final_query = db.session.query(TransferAccount)\
                    .join(user_search_result, user_search_result.c.default_transfer_account_id == TransferAccount.id)\
                    .execution_options(show_all=True)\
                    .order_by(db.text('rank DESC'))\
                    .filter(user_search_result.c.rank > 0.0)\
                    .filter(TransferAccount.is_ghost != True)
                transfer_accounts, total_items, total_pages = paginate_query(final_query, TransferAccount)
                result = transfer_accounts_schema.dump(transfer_accounts)
                data = { 'transfer_accounts': result.data }
            else:
                final_query = db.session.query(CreditTransfer)\
                    .join(user_search_result, 
                        or_(user_search_result.c.default_transfer_account_id == CreditTransfer.recipient_transfer_account_id,\
                        user_search_result.c.default_transfer_account_id == CreditTransfer.sender_transfer_account_id)
                    )\
                    .execution_options(show_all=True)\
                    .order_by(db.text('rank DESC'))\
                    .filter(user_search_result.c.rank > 0.0)
                credit_transfers, total_items, total_pages = paginate_query(final_query, CreditTransfer)
                result = credit_transfers_schema.dump(credit_transfers)
                data = { 'credit_transfers': result.data }

        response_object = {
            'message': 'Successfully Loaded.',
            'items': total_items,
            'pages': total_pages,
            'query_time': datetime.datetime.utcnow(),
            'data': data
        }

        bytes_data = orjson.dumps(response_object)
        resp = make_response(bytes_data, 200)
        resp.mimetype = 'application/json'
        return resp

search_blueprint.add_url_rule(
    '/search/',
    view_func=SearchAPI.as_view('search_view'),
    methods=['GET']
)
