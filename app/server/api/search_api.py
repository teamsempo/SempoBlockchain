from flask import Blueprint, request
from flask.views import MethodView
import re
import json

from server import db, bt
from server.schemas import transfer_accounts_schema
from server.models.search import SearchView
from sqlalchemy.sql.expression import func
from server.models.transfer_account import TransferAccount

search_blueprint = Blueprint('search', __name__)


class SearchAPI(MethodView):
    def get(self, search_string='m'):
       
        # Note: Using tsquery wildcards here. Good docs of them here:
        # https://www.postgresql.org/docs/current/datatype-textsearch.html#DATATYPE-TSQUERY
        # 'Fran deRoo' -> 'Fran:* | deRoo:*'
        # Matches strings like "Francine deRoos"
        # Will also match "Michiel deRoos" because of the or clause, but this will be ranked lower
        search_string = search_string.strip()
        tsquery = ''
        if len(search_string) > 0:
            search_terms = search_string.split(' ')
            tsquery = ':* | '.join(search_terms)+':*'

        # First get users who match search string
        user_search_result = db.session.query(
            db.distinct(SearchView.id),
            SearchView,
            # This ugly (but functional) multi-tscolumn ranking is a modified from Ben Smithgall's blog post
            # https://www.codeforamerica.org/blog/2015/07/02/multi-table-full-text-search-with-postgres-flask-and-sqlalchemy/
            db.func.max(db.func.full_text.ts_rank(
                db.func.setweight(db.func.coalesce(SearchView.tsv_email, ''), 'D').concat( # Priority D
                    db.func.setweight(db.func.coalesce(SearchView.tsv_phone, ''), 'A') # Priority A
                ).concat(
                    db.func.setweight(db.func.coalesce(SearchView.tsv_first_name, ''), 'B') # Priority B 
                ).concat(
                    db.func.setweight(db.func.coalesce(SearchView.tsv_last_name, ''), 'B') # Priority B 
                ), db.func.to_tsquery(tsquery, postgresql_regconfig='english')
            )).label('rank')
            ).group_by(
                SearchView,
            ).execution_options(show_all=True).subquery()

        # Then use those results to join aginst TransferAccount
        # TODO: Switch between joining against TransferAccount, and Transfers
        result = db.session.query(TransferAccount
            # Note: Manual join here since sqlalchemy doesn't support foreign keys in materialized views
            ).join(user_search_result, user_search_result.c.default_transfer_account_id == TransferAccount.id
            ).execution_options(show_all=True
            ).order_by(db.text('rank DESC')
            ).filter(user_search_result.c.rank > 0.0).all()
        print(result)
        result = transfer_accounts_schema.dump(result)
        return { 'data': {'transfer_accounts': result.data} }


search_blueprint.add_url_rule(
    '/search/',
    view_func=SearchAPI.as_view('search_view'),
    methods=['GET']
)




