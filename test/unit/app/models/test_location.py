import pytest

import logging

logg = logging.getLogger(__file__)

from helpers.factories import UserFactory 

def test_location_set_external(new_locations):

    new_locations['top'].add_external_data('OSM', {'foo': 'bar', 'baz': 42})
    new_locations['top'].add_external_data('GEONAMES', {'xyzzy': 666})
    
    assert len(new_locations['top'].location_external) == 2


def test_location_hierarchy(new_locations):
    assert new_locations['leaf'].parent == new_locations['node']
    assert new_locations['node'].parent == new_locations['top']


def test_user_location_link(test_client, new_locations):

    user = UserFactory(first_name='Melvin', last_name='Ferd')
    user.full_location = new_locations['leaf']

    assert user.full_location.common_name == new_locations['leaf'].common_name

