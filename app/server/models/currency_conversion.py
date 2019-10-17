from server import db
from server.models.utils import ModelBase


class CurrencyConversion(ModelBase):
    __tablename__ = 'currency_conversion'

    code = db.Column(db.String)
    rate = db.Column(db.Float)
