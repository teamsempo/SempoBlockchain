from server import db
from server.models.utils import ModelBase
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func

class CustomAttributeUserStorage(ModelBase):
    __tablename__ = 'custom_attribute_user_storage'

    custom_attribute_id = db.Column(db.Integer, db.ForeignKey('custom_attribute.id'), index=True)
    custom_attribute = db.relationship("CustomAttribute", back_populates="attributes")

    name = db.Column(db.String) # Deprecated for key
    value = db.Column(db.String)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    uploaded_image_id = db.Column(db.Integer)

    @hybrid_property
    def key(self):
        return self.custom_attribute.name
