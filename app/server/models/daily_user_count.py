from server import db
from server.models.utils import ModelBase
import datetime

class DailyUserCount(ModelBase):
    __tablename__ = 'daily_user_count'
    date = db.Column(db.DateTime)
    count = db.Column(db.Integer)