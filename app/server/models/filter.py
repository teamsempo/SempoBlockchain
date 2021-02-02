from server import db
from server.models.utils import ModelBase, OneOrgBase

class Filter(OneOrgBase, ModelBase):
    __tablename__ = 'filter'

    name = db.Column(db.String)
    filter = db.Column(db.String)
