from server import db
from server.models.utils import ModelBase


class CustomAttribute(ModelBase):
    __tablename__ = 'custom_attribute'

    name = db.Column(db.String)
    attributes = db.relationship("CustomAttributeUserStorage", back_populates="custom_attribute")
