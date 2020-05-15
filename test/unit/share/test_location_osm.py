"""Tests location data resource workers
"""

# standard imports
import logging

# third party imports
import pytest

# platform imports
import config
from server import db
from server.models.location import Location
from share.location.osm import osm_resolve_name, osm_resolve_coordinates
from share.location.enum import LocationExternalSourceEnum

logg = logging.getLogger(__file__)


class LocationCacheControl:

    def __init__(self):
        self.place_id = 0
        self.location = None

    def have_osm_data(self, place_id):
        if self.location != None:
            raise RuntimeError('cached location already set')
        self.location = Location.get_by_custom(LocationExternalSourceEnum.OSM, 'place_id', place_id)
        if self.location != None:
            self.place_id = place_id
        return self.location


# TODO: improve by using object to hold cached location item which has have_osm_data as class method
def store_osm_data(location_data, cache):

    locations = []

    logg.debug('data {} count {}'.format(location_data, len(location_data)))
    for i in range(len(location_data)):
        location = None
        if cache.location != None:
            if location_data[i]['ext_data']['place_id'] == cache.place_id:
                location = Location.get_by_custom(LocationExternalSourceEnum.OSM, 'place_id', location_data[i]['ext_data']['place_id'])
        if location == None:
            location = Location(
                location_data[i]['name'],
                location_data[i]['latitude'],
                location_data[i]['longitude'],
                    )
            location.add_external_data(LocationExternalSourceEnum.OSM, location_data[i]['ext_data'])
        locations.append(location)
        logg.debug('adding {}'.format(location))
    
    for i in range(len(locations)):
        location = locations[i]
        logg.debug(location.location_external[0].external_reference)
        if location.location_external[0].external_reference['place_id'] == cache.place_id:
            break
        if i < len(locations)-1:
            locations[i].set_parent(locations[i+1])
        db.session.add(locations[i])
    db.session.commit()
    return locations


def test_get_osm_cascade(test_client, init_database):
    """
    GIVEN a search string
    WHEN hierarchical matches exist in osm for that string
    THEN check that location and relations are correctly returned
    """

    cache = LocationCacheControl()
    q = 'mnarani'
    location_data = osm_resolve_name(q, storage_check_callback=cache.have_osm_data)
    locations = store_osm_data(location_data, cache)
    
    leaf = locations[0]
    assert leaf != None
    assert leaf.common_name.lower() == q

    parent = leaf.parent
    assert parent.common_name.lower() == 'kilifi'

    parent = parent.parent
    assert 'kenya' in parent.common_name.lower() 
    logg.debug('leaf {} parent {}'.format(leaf, parent))


def test_get_osm_cascade_coordinates(test_client, init_database):
    """
    GIVEN coordinates
    WHEN hierarchical matches exist in osm for that coordinates
    THEN check that location and relations are correctly returned
    """

    cache = LocationCacheControl()
    q = 'mnarani'
    latitude = -3.6536
    longitude = 39.8512
    location_data = osm_resolve_coordinates(latitude, longitude, storage_check_callback=cache.have_osm_data)
    locations = store_osm_data(location_data, cache)

    leaf = locations[0]
    assert leaf != None
    assert leaf.common_name.lower() == q

    parent = leaf.parent
    assert parent.common_name.lower() == 'kilifi'

    parent = parent.parent
    assert 'kenya' in parent.common_name.lower() 
    logg.debug('leaf {} parent {}'.format(leaf, parent))

