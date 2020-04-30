# standard imports
import logging

# third party imports
import pytest

# platform imports
import config
from server.models import Location
from other_worker.location import search_name_from_osm


logg = logging.getLogger(__file__)

@pytest.mark.skipif(getattr(config, 'TEST_EXTERNAL_SERVICE', None) == None, reason='config.TEST_EXTERNAL_SERVICE not set')
def test_get_osm_cascade(test_client, init_database):
    q = 'mnarani'
    leaf = search_name_from_osm('mnarani')
    assert leaf.common_name.lower() == q

    parent = leaf.parent
    assert parent.common_name.lower() == 'kilifi'

    parent = parent.parent
    assert 'kenya' in parent.common_name.lower() 
    logg.debug(leaf, parent)
