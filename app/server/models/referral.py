from sqlalchemy.ext.hybrid import hybrid_property

from server import db
from server.models.utils import ModelBase
from server.models.user import User
from server.utils.phone import proccess_phone_number


class Referral(ModelBase):
    __tablename__ = 'referral'

    first_name              = db.Column(db.String)
    last_name               = db.Column(db.String)
    reason                  = db.Column(db.String)

    _phone                  = db.Column(db.String())

    @hybrid_property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, phone):
        self._phone = proccess_phone_number(phone)

    referring_user_id     = db.Column(db.Integer, db.ForeignKey(User.id))

