from sqlalchemy.dialects.postgresql import JSON

from server import db
from server.models.utils import ModelBase, OneOrgBase


class Settings(OneOrgBase, ModelBase):
    __tablename__ = 'settings'

    name = db.Column(db.String)
    type = db.Column(db.String)
    value = db.Column(JSON)
