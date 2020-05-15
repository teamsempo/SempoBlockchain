"""Location models

Provides the classes Location and LocationExternal which represent hierarchically
ordered physical locations.
"""

# standard imports
import hashlib
import logging

# framework imports
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy import text

# platform imports
from server import db
from server.models.utils import ModelBase
from share.location.enum import LocationExternalSourceEnum

logg = logging.getLogger(__file__)


class LocationExternal(db.Model):
    """SqlAlchemy model class that Maps data from external map resources
    like Openstreetmaps and Geonames to raw GPS location data.

    Attributes
    ----------
    id : int
        database primary key.
    source : enum
        external source identifier.
    external_reference : dict
        external source data
    location_id : int
        foreign key for one-to-one reference to related Location object.
    
    Args
    ----
    location : Location
        location object foreign relation.
    source : enum
        external source identifier.
    reference_data : dict
        external source data.

    """
    
    __tablename__ = 'location_external'

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.Enum(LocationExternalSourceEnum))
    external_reference = db.Column(JSONB)

    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))


    # TODO: verify how it will behave with nested data
    @staticmethod
    def digest(enum_key: str, data_dict: dict):
        """static method that calculates the digest from canonical representation of
        the source and external_reference attributes.
           
        Parameters
        ----------
        enum_key : str
            string value of source enum
        data_dict: dict
            external_reference value in dictionary form
        """
        h = hashlib.sha1()
        h.update(enum_key.encode('utf-8'))
        for k in sorted(data_dict):
            v = str(data_dict[k])
            h.update(k.encode('utf-8'))
            h.update(v.encode('utf-8'))
        return h.digest()


    def is_same(self, source, references_data):
        """Evaluate whether the canonical representation of the provided source and
        references_data match the ones stored in the instance.

        Parameters
        ----------
        source : enum
            external source identifier
        references_data : dict
            external source data

        Returns
        -------
        matches : bool
        """

        ours = LocationExternal.digest(source.value, self.external_reference)
        theirs = LocationExternal.digest(source.value, references_data)
        return ours == theirs


    @staticmethod
    def get_by_custom(source_enum, key, value):
        """Static method which searches for the given key/value pair
        in external references.

        Parameters
        ----------
        source_enum : enum
            external source identifier
        key : str
            key to match
        value : str
            value to match

        Returns
        -------
        external : list
            list of matches external objects
        """

        sql = text('SELECT id, location_id FROM location_external WHERE source = :s and external_reference ->> :k = :v')
        sql = sql.bindparams(k=key, v=str(value), s=source_enum.value)
        rs = db.session.get_bind().execute(sql)
        exts = []
        for le in rs.fetchall():
            logg.debug('item {}'.format(le[0]))
            exts.append(LocationExternal.query.get(le[0]))
        return exts

    def __init__(self, location, source, references_data, **kwargs):
        super(LocationExternal, self).__init__(**kwargs)
        self.source = source
        self.external_reference = references_data
        self.location_id = location.id


class Location(db.Model):
    """SqlAlchemy model class representing a hierarchical relations between actual
    physical locations.

    Attributes
    ----------
    common_name : str
        well-known name of the location
    latitude : float
        coordinate value 
    longitude : float
        coordinate value 
    parent_id : int
        foreign key of parent location
    parent : Location
        parent location
    location_external : list
        associated LocationExternal objects

    Args
    ----
    common_name : str
        well-known name of the location
    latitude : float
        coordinate value 
    longitude : float
        coordinate value 
    parent : Location
        parent location
    **kwargs : dict
        variable-length args to pass to superclass
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
        """Set parent location
        """
        if self.parent != None:
            raise ValueError('parent already set')
        self.parent = parent


    def add_external_data(self, source, references_data):
        """Create new external data source for location

        Parameters
        ----------
        source : enum
            external source identifier
        references_data : dict
            external source data
        """

        self.location_external.append(LocationExternal(self, source, references_data)) 


    def is_same_external_data(self, source, references_data):
        """see LocationExternal.is_same()

        Parameters
        ----------
        source : enum
            external source identifier
        references_data : dict
            external source data

        Returns
        -------
        match : bool
        """

        if len(self.location_external) == 0:
            return False
        return self.location_external[0].is_same(source, references_data)


    @staticmethod
    def get_by_custom(source_enum, key, value):
        """see also LocationExternal.get_by_custom()

        Parameters
        ----------
        source_enum : enum
            external source identifier
        key : str
            key to match
        value : str
            value to match

        Returns
        -------
        external : list
            list of matches external objects
        """
        r = LocationExternal.get_by_custom(source_enum, key, value)
        if len(r) == 0:
            return None
        l = Location.query.get(r[0].location_id)
        return l


    def __init__(self, common_name, latitude, longitude, parent=None, **kwargs):
        super(Location, self).__init__(**kwargs)
        self.common_name = common_name
        self.latitude = latitude
        self.longitude = longitude
        if parent != None:
            self.set_parent(parent)
