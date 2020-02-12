from flask import Blueprint, request
from flask.views import MethodView
import re
import json
from server import db, bt

from server.models.search import SearchView
from sqlalchemy.sql.expression import func
from server.models.transfer_account import TransferAccount

search_blueprint = Blueprint('search', __name__)


class SearchAPI(MethodView):
    def get(self, search_string='mic'):
       
        # Note: Using tsquery wildcards here. Good docs of them here:
        # https://www.postgresql.org/docs/current/datatype-textsearch.html#DATATYPE-TSQUERY
        # 'Fran deRoo' -> 'Fran:* | deRoo:*'
        # Matches strings like "Francine deRoos"
        # Will also match "Michiel deRoos" because of the or clause, but this will be ranked lower
        search_terms = search_string.split(' ')
        tsquery = ':* | '.join(search_terms)+':*'

        query_result = db.session.query(
            db.distinct(SearchView.id),
            SearchView.first_name,
            SearchView.last_name,
            SearchView.email,
            SearchView._phone,
            SearchView.default_transfer_account_id,
            TransferAccount._balance_wei,
            # This ugly (but functional) multi-tscolumn ranking is modified from Ben Smithgall's great guide
            # https://www.codeforamerica.org/blog/2015/07/02/multi-table-full-text-search-with-postgres-flask-and-sqlalchemy/
            db.func.max(db.func.full_text.ts_rank(
                db.func.setweight(db.func.coalesce(SearchView.tsv_email, ''), 'D').concat(
                    db.func.setweight(db.func.coalesce(SearchView.tsv_phone, ''), 'A')
                ).concat(
                    db.func.setweight(db.func.coalesce(SearchView.tsv_first_name, ''), 'B')
                ).concat(
                    db.func.setweight(db.func.coalesce(SearchView.tsv_last_name, ''), 'B')
                ), db.func.to_tsquery(tsquery, postgresql_regconfig='english')
            )).label('rank')
            ).join(TransferAccount, TransferAccount.id == SearchView.default_transfer_account_id).group_by(
                SearchView.id, SearchView.first_name, SearchView.last_name, SearchView.email, SearchView._phone, SearchView.default_transfer_account_id, TransferAccount._balance_wei
            ).order_by(db.text('rank DESC')
            ).execution_options(show_all=True).all()
        return {'results': query_result}

search_blueprint.add_url_rule(
    '/search/',
    view_func=SearchAPI.as_view('search_view'),
    methods=['GET']
)




