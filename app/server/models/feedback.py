from server import db
from server.models.utils import ModelBase
from server.models.user import User


class Feedback(ModelBase):
    __tablename__ = 'feedback'

    question                = db.Column(db.String)
    rating                  = db.Column(db.Float)
    additional_information  = db.Column(db.String)

    user_id                 = db.Column(db.Integer, db.ForeignKey(User.id))
