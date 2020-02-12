from flask import Blueprint, request
from flask.views import MethodView
import re
import json

from server import db, bt
from server.utils.auth import requires_auth
from server.schemas import transfer_accounts_schema
from server.models.search import SearchView
from sqlalchemy.sql.expression import func
from server.models.transfer_account import TransferAccount

search_blueprint = Blueprint('search', __name__)


class SearchAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'any'})
    def get(self, search_string=''):
        search_string = request.args.get('search_string') or ''
        # Note: Using tsquery wildcards here. Good docs of them here:
        # https://www.postgresql.org/docs/current/datatype-textsearch.html#DATATYPE-TSQUERY
        # 'Fran deRoo' -> 'Fran:* | deRoo:*'
        # Matches strings like "Francine deRoos"
        # Will also match "Michiel deRoos" because of the or clause, but this will be ranked lower
        search_terms = search_string.strip().split(' ')
        tsquery = ':* | '.join(search_terms)+':*'
        if search_string == '':
            all_transfer_accounts = TransferAccount.query.filter(TransferAccount.is_ghost != True)\
            .execution_options(show_all=True)\
            .all()
            result = transfer_accounts_schema.dump(all_transfer_accounts)
            return { 'data': {'transfer_accounts': result.data} }

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
                    .concat(db.func.setweight(db.func.coalesce(SearchView.tsv_last_name, ''), 'B')),
                    db.func.to_tsquery(tsquery, postgresql_regconfig='english')))\
            .label('rank'))\
            .group_by(SearchView)\
            .subquery()

        # Then use those results to join aginst TransferAccount
        # TODO: Switch between joining against TransferAccount, and Transfers
        searched_transfer_accounts = db.session.query(TransferAccount)\
            .join(user_search_result, user_search_result.c.default_transfer_account_id == TransferAccount.id)\
            .execution_options(show_all=True)\
            .order_by(db.text('rank DESC'))\
            .filter(user_search_result.c.rank > 0.0)\
            .filter(TransferAccount.is_ghost != True)\
            .all()
        
        result = transfer_accounts_schema.dump(searched_transfer_accounts)
        return { 'data': {'transfer_accounts': result.data} }


search_blueprint.add_url_rule(
    '/search/',
    view_func=SearchAPI.as_view('search_view'),
    methods=['GET']
)

