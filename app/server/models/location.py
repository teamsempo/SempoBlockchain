from sqlalchemy.dialects.postgresql import JSON, JSONB

from server import db
from server.models.utils import ModelBase

from share.location import LocationExternalSourceEnum

class LocationExternal(db.Model):
    """Maps external map resources to location
    """
    
    __tablename__ = 'location_external'

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.Enum(LocationExternalSourceEnum))
    external_reference = db.Column(JSONB)

    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    

    def __init__(self, location, source, references_data, **kwargs):
        super(LocationExternal, self).__init__(**kwargs)
        self.source = source
        self.external_reference = references_data
        self.location_id = location.id


class Location(db.Model):
    """User extension table describing the user's location
    """

    __tablename__ = 'location'

    id = db.Column(db.Integer, primary_key=True)
    common_name = db.Column(db.String())
    latitude = db.Column(db.Numeric)
    longitude = db.Column(db.Numeric)
    parent_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    parent = db.relationship('Location', remote_side=[id])

    location_external = db.relationship('LocationExternal',
            lazy=True)

    def add_external_data(self, source, references_data):
        self.location_external.append(LocationExternal(self, source, references_data)) 

    def __init__(self, common_name, latitude, longitude, parent=None, **kwargs):
        super(Location, self).__init__(**kwargs)
        self.common_name = common_name
        self.latitude = latitude
        self.longitude = longitude
        if parent != None:
            self.parent = parent
