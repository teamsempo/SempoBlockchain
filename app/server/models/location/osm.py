# framework imports
from sqlalchemy.orm.attributes import flag_modified

# platform imports
from server.models.location import LocationExternal

class OSMLocationExternal(LocationExternal):

    def set_osm_id(self, osm_id):
        self.external_reference['osm_id'] = osm_id
        flag_modified(self, 'external_reference')

    def set_place_id(self, place_id):
        self.external_reference['place_id'] = place_id
        flag_modified(self, 'external_reference')

    def __init__(self, location, source, references_data, **kwargs):
        super(LocationExternal, self).__init__(**kwargs)
