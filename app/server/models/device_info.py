from server import db
from server.models.utils import ModelBase
from server.models.user import User

class DeviceInfo(ModelBase):
    __tablename__ = 'device_info'

    serial_number   = db.Column(db.String)
    unique_id       = db.Column(db.String)
    brand           = db.Column(db.String)
    model           = db.Column(db.String)

    height          = db.Column(db.Integer)
    width           = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
