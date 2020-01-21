from sqlalchemy.dialects.postgresql import JSON

from server import db
from server.models.utils import ModelBase, OneOrgBase


class SavedFilter(OneOrgBase, ModelBase):
    __tablename__ = 'saved_filter'

    name = db.Column(db.String)
    filter = db.Column(JSON)

    def __init__(self, **kwargs):
        super(SavedFilter, self).__init__(**kwargs)
