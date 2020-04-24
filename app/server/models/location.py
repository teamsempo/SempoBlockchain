from sqlalchemy.dialects.postgresql import JSON, JSONB

from server import db
from server.models import User
from server.models.utils import ModelBase

from share.location import LocationExternalSourceEnum

class LocationExternal(ModelBase):
    """Maps external map resources to location
    """
    
    __tablename__ = 'location_external'

    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    source = db.Column(db.Enum(LocationExternalSourceEnum))
    external_reference = db.Column(JSONB)


class Location(ModelBase):
    """User extension table describing the user's location
    """

    __tablename__ = 'location'

    id = db.Column(db.Integer, primary_key=True)
    common_name = db.Column(db.String())
    latitude = db.Column(db.Numeric)
    longitude = db.Column(db.Numeric)
    parent_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    parent = db.relationship('Location', remote_side=[id])

    external_sources = db.relationship('LocationExternal',
            primaryjoin='LocationExternal.location_id == Location.id',
            lazy=True)

    def __init__(self, common_name, latitude, longitude, parent=None, **kwargs):
        super(Location, self).__init__(**kwargs)
        self.common_name = common_name
        self.latitude = latitude
        self.longitude = longitude
        if parent != None:
            self.parent = parent
