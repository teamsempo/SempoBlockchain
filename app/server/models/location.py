# standard imports
import hashlib

# framework imports
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy import text

# platform imports
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

    # TODO: unconfirmed how this acts with nested data
    @staticmethod
    def Digest(enum_key: str, data_dict: dict):
        h = hashlib.sha1()
        h.update(source.value)
        for k in sorted(data_dict):
            v = str(data_dict[k])
            h.update(k.encode('utf-8'))
            h.update(v.encode('utf-8'))
        return h.digest()

    def is_same(self, source, references_data):
        ours = LocationExternal.Digest(self.source.value, self.external_reference)
        theirs = LocationExternal.Digest(source, references_data)
        return ours == theirs

    @staticmethod
    def get_by_custom(source_enum, key, value):
        sql = text('SELECT location_id FROM location_external WHERE source = :s and external_reference ->> :k = :v')
        sql = sql.bindparams(k=key, v=str(value), s=source_enum.value)
        rs = db.session.get_bind().execute(sql)
        return rs.fetchall()

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

   
    def set_parent(self, parent):
        if self.parent != None:
            raise ValueError('parent already set')
        self.parent = parent

    def add_external_data(self, source, references_data):
        self.location_external.append(LocationExternal(self, source, references_data)) 

    def is_same_external_data(self, source, references_data):
        return self.location_external.is_same(source, references_data)

    def get_external_data_hash(self):
        return self.location_external.digest()
    
    def __init__(self, common_name, latitude, longitude, parent=None, **kwargs):
        super(Location, self).__init__(**kwargs)
        self.common_name = common_name
        self.latitude = latitude
        self.longitude = longitude
        if parent != None:
            self.set_parent(parent)
