from server import db
from server.models.utils import ModelBase
from server.models.custom_attribute import CustomAttribute
from sqlalchemy import cast
from sqlalchemy.ext.hybrid import hybrid_property

from sqlalchemy import func

from server.models.custom_attribute import CustomAttribute

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

    @staticmethod
    def get_attributes_and_options():
        # Get all custom attributes
        attributes = db.session.query(CustomAttribute).all()
        attribute_options = {}
        # Get all possible options for those attributes
        for a in attributes:
            options = db.session.query(CustomAttributeUserStorage.value)\
                .filter(CustomAttributeUserStorage.custom_attribute_id == a.id)\
                .distinct()\
                .all()
            options = [o[0] for o in options]
            attribute_options[a.name] = options
        return attribute_options
