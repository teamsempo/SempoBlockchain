from server import db
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.sql.functions import GenericFunction

# Note: this represents a matrerialized view.
# Changes here will NOT automatically turn into database migrations
class SearchView(db.Model):
    __tablename__ = 'search_view'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String)
    _phone = db.Column(db.String)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    tsv_email = db.Column(TSVECTOR)
    tsv_phone = db.Column(TSVECTOR)
    tsv_first_name = db.Column(TSVECTOR)
    tsv_last_name = db.Column(TSVECTOR)
    default_transfer_account_id = db.Column(db.Integer)

class TSRank(GenericFunction):
    package = 'full_text'
    name = 'ts_rank'
