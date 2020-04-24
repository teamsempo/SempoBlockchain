from server import db

from server.models.location import Location

class UserExtension(db.Model):
    __tablename__ = 'user_extension_association_table'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), primary_key=True)
    location = db.relationship(Location)
