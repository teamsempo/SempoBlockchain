import enum

osm_extension_fields = ['place_id', 'osm_id']

class LocationExternalSourceEnum(enum.Enum):
    OSM = 'OSM'
    GEONAMES = 'GEONAMES'

