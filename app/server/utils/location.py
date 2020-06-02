from typing import Tuple, Optional
import requests
from sentry_sdk import capture_message

from config import logg
from server import db, executor
from server.models.user import User

@executor.job
def async_set_user_gps_from_location(user_id: int, location: str):
    """
    Basic threaded process to set a users gps location based off a provided location string.
    Doesn't attempt retries or anything fancy. Wraps the function below for testing purposes

    :param user_id: the user to set the location for
    :param location: a location string such as 'State Library of Victoria' or '328 Swanston St, Melbourne'
    """
    _set_user_gps_from_location(user_id, location)


def _set_user_gps_from_location(user_id: int, location: str):
    """
    Wrapped version for testing
    """
    gps_tuple = osm_location_to_gps_lookup(location)
    if not gps_tuple:
        logg.warning(f'GPS for location not found on OSM for user {user_id}')
        return

    lat, lng = gps_tuple

    user = User.query.get(user_id)
    if not user:
        capture_message(f'User not found for id {user_id}')
        return

    user.lat = lat
    user.lng = lng

    db.session.commit()


def osm_location_to_gps_lookup(location: str) -> Optional[Tuple[float, float]]:
    """
    OpenStreetMap GPS location lookup.
    Returns none if the location is not found, or the first result if there are multiple matches

    :param location: a string address such as '328 Swanston St, Melbourne'
     or search query such as 'State Library of Victoria'
    :return: a (latitude, longitude) tuple if the address is found, or none if there's some issue
    """

    r = _query_osm(location)

    if r.status_code != 200:
        # OSM should never hit this under normal operation, even with a unrecognised location, so capture error
        capture_message(f'OSM {r.status_code} Status Code. Text: {r.text}')
        return None

    json = r.json()

    if len(json) == 0:
        # Being unable to recognise locations to GPS is common, so don't bother raising an error
        return None

    lat = float(json[0]['lat'])
    lng = float(json[0]['lon'])

    return (lat, lng)


def _query_osm(location):
    """
    Minimal osm query, split out for efficient mocking in tests
    :param location: location string
    :return: query response
    """
    return requests.get(
        'https://nominatim.openstreetmap.org/search',
        params={
            'format': 'json',
            'q': location
        }
    )
