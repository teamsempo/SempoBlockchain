"""Tests the physical location model and its relation as a User extension.
"""

# standard imports
import pytest
import logging

# platform imports
from server import db
from helpers.factories import UserFactory 
from server.models import Location
from share.location.enum import LocationExternalSourceEnum

logg = logging.getLogger(__file__)


def test_location_hierarchy(new_locations):
    """
    GIVEN a set of related locations
    THEN check that relation is correct
    """

    assert new_locations['leaf'].parent == new_locations['node']
    assert new_locations['node'].parent == new_locations['top']


def test_location_set_external(test_client, new_locations):
    """
    GIVEN a set of related locations
    WHEN external source data is added to one
    THEN check that it is stored and that a search on the external data uniquely returns the entry
    """

    ext_data_osm = {'foo': 'bar', 'baz': 42}
    ext_data_geonames = {'xyzzy': 666}
    new_locations['top'].add_external_data(LocationExternalSourceEnum.OSM.value, ext_data_osm)
    new_locations['top'].add_external_data(LocationExternalSourceEnum.GEONAMES.value, ext_data_geonames)
    db.session.commit()

    assert len(new_locations['top'].location_external) == 2

    ext = Location.get_by_custom(LocationExternalSourceEnum.OSM, 'foo', 'bar')
    assert ext != None
    logg.debug(new_locations['top'])
    assert ext == new_locations['top']

    assert new_locations['top'].is_same_external_data(LocationExternalSourceEnum.OSM, ext_data_osm)
    assert not new_locations['leaf'].is_same_external_data(LocationExternalSourceEnum.OSM, ext_data_osm)
    assert not new_locations['top'].is_same_external_data(LocationExternalSourceEnum.OSM, ext_data_geonames)
    assert not new_locations['top'].is_same_external_data(LocationExternalSourceEnum.GEONAMES, ext_data_geonames)



def test_user_location_link(test_client, new_locations):
    """
    GIVEN a location
    WHEN it is linked to a user
    THEN check that the relation is stored
    """

    user = UserFactory(first_name='Melvin', last_name='Ferd')
    user.full_location = new_locations['leaf']

    assert user.full_location.common_name == new_locations['leaf'].common_name
