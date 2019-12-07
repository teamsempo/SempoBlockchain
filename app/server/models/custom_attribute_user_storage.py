from server import db
from server.models.utils import ModelBase


class CustomAttributeUserStorage(ModelBase):
    __tablename__ = 'custom_attribute_user_storage'

    name = db.Column(db.String)
    value = db.Column(db.JSON)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_image_id = db.Column(db.Integer)
