from sqlalchemy.dialects.postgresql import JSON

from server import db
from server.models.utils import ModelBase


class SavedFilter(ModelBase):
    __tablename__ = 'saved_filter'

    name = db.Column(db.String)
    filter = db.Column(JSON)
