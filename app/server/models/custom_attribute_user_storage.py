from server import db
from server.models.utils import ModelBase
from sqlalchemy import cast

class CustomAttributeUserStorage(ModelBase):
    __tablename__ = 'custom_attribute_user_storage'

    name = db.Column(db.String)
    value = db.Column(db.JSON)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_image_id = db.Column(db.Integer)

    @staticmethod
    def get_attributes_and_options():
        # Get all custom attributes
        attributes = [u.name for u in db.session.query(CustomAttributeUserStorage.name).distinct()]
        # Get all possible options for those attributes
        attribute_options = {}
        for a in attributes:
            attribute_options[a] = [
                u[0].replace('"', '') for u in db.session.query(cast(CustomAttributeUserStorage.value, db.String))
                .filter(CustomAttributeUserStorage.name == a)
                .distinct()
            ]
        return attribute_options
