"""Association model for extended user data

Currently provides the following extensions:

    * Location
"""

# platform imports
from server import db
from server.models.location import Location


class UserExtension(db.Model):
    """SqlAlchemy model that holds all extensions to a User object

    Attributes
    ----------
    user_id : int
        id of User
    location_id : int
        foreign key of location relation
    location : Location
        location relation
    """
    __tablename__ = 'user_extension_association_table'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), primary_key=True)
    location = db.relationship(Location)
