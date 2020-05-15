"""Worker task for resolving location data from openstreetmap.

Adds location and its parent relations to database.
"""

# standard imports
import urllib
import requests
import logging
import json
import sys

logg = logging.getLogger(__file__)
logg.debug(sys.path)
# platform imports
import config
from share.location.enum import LocationExternalSourceEnum, osm_extension_fields

# local imports
from .constants import QUERY_TIMEOUT, DEFAULT_COUNTRY_CODE, VALID_OSM_ENTRY_TYPES



def osm_get_detail(place_id : int):

    url = 'https://nominatim.openstreetmap.org/details?format=json&linkedplaces=1&place_id=' 

    # build and perform osm query
    response = requests.get('{}{}'.format(url, place_id), timeout=QUERY_TIMEOUT)
    if response.status_code != 200:
        e = LookupError('failed request to openstreetmap; status code {}'.format(response.status_code))
        raise(e)
    response_json = json.loads(response.text)
    logg.debug(response_json)
    return response_json


def osm_get_place_hierarchy(place_id : int, storage_check_callback=None):
    """Retrieves details from the OSM HTTP endpoint of the matching place_id,
    and recursively retrieves its parent relation places. The results are returned as location dict objects

    Location dict object has the following structure:

    {
        'name': common name of location
        'latitude': latitude
        'longitude': longitude
        'ext_type': osm location type enum
        'ext_data': dict with osm specific fields
    }

    If storage_check_callback is given, a return value other than None will signal to the loop that the location is already known,
    That location is then added to the list, and the loop is terminated.


    Parameters
    ----------
    place_id : int
        osm place_id of start node
    storage_check_callback : function
        callback to check existence of location in caller

    Returns
    -------
    locations : list
        all resolved locations as location dict objects not already existing according to storage check callback
        in hierarchical order from lowest (start node) to highest

    """

    locations = []

    # iterate until parent relation is 0
    next_place_id = place_id
    last_is_cached = False
    while next_place_id != 0:

        # check if data already exists, if so, return prematurely as within that location relation
        # the caller has everything it nneeds
        new_location = {}
        ext_data = {}

        if storage_check_callback != None:
            r = storage_check_callback(next_place_id)
            if r != None:
                new_location['name'] = r.common_name
                new_location['latitude'] = r.latitude
                new_location['longitude'] = r.longitude
                new_location['ext_type'] = LocationExternalSourceEnum.OSM
                new_location['ext_data'] = {}
                new_location['ext_data']['place_id'] = next_place_id
                locations.append(new_location)
                break
       
        response_json = osm_get_detail(next_place_id)
        current_place_id = next_place_id
        next_place_id = response_json['parent_place_id']
        if response_json['type'] == 'unclassified':
            logg.debug('place id {} is unclassified, get parent {}'.format(current_place_id, next_place_id))
            continue
       
        # create new location object and add it to list 
        new_location = {
                'name': response_json['names']['name'],
                'latitude': response_json['centroid']['coordinates'][0],
                'longitude': response_json['centroid']['coordinates'][1],
                }

        for field in osm_extension_fields:
            ext_data[field] = response_json[field]

        new_location['ext_type'] = LocationExternalSourceEnum.OSM
        new_location['ext_data'] = ext_data
        locations.append(new_location)

    return locations


def osm_resolve_name(name : str, country=DEFAULT_COUNTRY_CODE, storage_check_callback=None):
    """Searches the OSM HTTP endpoint for a location name. If a match is found
    the location hierarchy is built and committed to database.

    Parameters
    ----------
    name : str
        name to search
    country : str
        country filter (default: const DEFAULT_COUNTRY_CODE)
    
    Returns
    -------
    location : Location
        created / retrieved location object. If none is found, None is returned.
    """

    # build osm query
    query = {
            'format': 'json',
            'dedupe': 1,
            'country': country, 
            'q': name,
            }
    if getattr(config, 'EXT_OSM_EMAIL', None):
        query['email'] = config.EXT_OSM_EMAIL
    query_string = urllib.parse.urlencode(query)

    # perform osm query
    url = 'https://nominatim.openstreetmap.org/search?' + query_string
    try:
        response = requests.get(url, timeout=QUERY_TIMEOUT)
    except requests.exceptions.Timeout:
        logg.warning('request timeout to openstreetmap; {}:{}'.format(country, name))
        return None
    if response.status_code != 200:
        logg.warning('failed request to openstreetmap; {}:{}'.format(country, name))
        return None

    response_json = json.loads(response.text)
    logg.debug(response_json)

    # identify a suitable record among those returned
    place_id = 0
    for place in response_json:
        if place['type'] in VALID_OSM_ENTRY_TYPES:
            place_id = place['place_id']
    if place_id == 0:
        logg.debug('no suitable record found in openstreetmap for {}:{}'.format(country, name))
        return None

    # get related locations not already in database
    locations = []
    try:
        locations = osm_get_place_hierarchy(place_id, storage_check_callback)
    except LookupError as e:
        logg.warning('osm hierarchical query for {}:{} failed (response): {}'.format(country, name, e))
    except requests.exceptions.Timeout as e:
        logg.warning('osm hierarchical query for {}:{} failed (timeout): {}'.format(country, name, e))
                 
#    # set hierarchical relations and store in database
#    for i in range(len(locations)-1):
#        locations[i].set_parent(locations[i+1])
#        db.session.add(locations[i])
#    db.session.commit()

    return locations


def osm_resolve_coordinates(latitude, longitude, storage_check_callback=None):
  
    query = {
        'format': 'json',
        'lat': latitude,
        'lon': longitude,
    }

    if getattr(config, 'EXT_OSM_EMAIL', None):
        q['email'] = config.EXT_OSM_EMAIL
    query_string = urllib.parse.urlencode(query)

    # perform osm query
    url = 'https://nominatim.openstreetmap.org/reverse?' + query_string
    try:
        response = requests.get(url, timeout=QUERY_TIMEOUT)
    except requests.exceptions.Timeout:
        logg.warning('request timeout to openstreetmap; {}:{}'.format(country, name))
        return None
    if response.status_code != 200:
        logg.warning('failed request to openstreetmap; {}:{}'.format(country, name))
        return None

    response_json = json.loads(response.text)
    logg.debug(response_json)

    # identify a suitable record among those returned
    place_id = 0
    place = response_json
    #if place['osm_type'] in VALID_OSM_ENTRY_TYPES:
    place_id = place['place_id']
    if place_id == None or place_id == 0:
        logg.debug('no suitable record found in openstreetmap for N{}/E{}'.format(latitude, longitude))
        return None

    # skip the first entry if it is unclassified
    #response_json = osm_get_detail

    # get related locations not already in database
    locations = []
    try:
        locations = osm_get_place_hierarchy(place_id, storage_check_callback)
    except LookupError as e:
        logg.warning('osm hierarchical query for {}:{} failed (response): {}'.format(country, name, e))
    except requests.exceptions.Timeout as e:
        logg.warning('osm hierarchical query for {}:{} failed (timeout): {}'.format(country, name, e))
                 
    return locations
