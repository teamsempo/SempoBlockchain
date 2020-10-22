import pytest

from server.utils.location import (
    osm_location_to_gps_lookup,
    _set_user_gps_from_location
)

@pytest.mark.parametrize("location, expected_coordinates", [
    ("fooplace", (-37.81, 144.97)),
    ("multiple matched place", (12.0, 14.4)),
    ("not a real place", None)
])
def test_osm_lookup(location, expected_coordinates):
    assert osm_location_to_gps_lookup(location) == expected_coordinates


@pytest.mark.parametrize("location, expected_coordinates", [
    ("not a real place", (None, None)),
    ("fooplace", (-37.81, 144.97)),
    ("multiple matched place", (12.0, 14.4)),
    ("multiple matched place, Canada", (12.0, 14.4)), # Makes sure country isn't added twice (I.e. 'multiple matched place, Canada, Canada')
])
def test_set_location(create_transfer_account_user, location, expected_coordinates):
    create_transfer_account_user.default_organisation.country_code = 'CA'
    _set_user_gps_from_location(create_transfer_account_user.id, location)
    assert create_transfer_account_user.lat == expected_coordinates[0]
    assert create_transfer_account_user.lng == expected_coordinates[1]

