# standard imports
import requests
import logging
import json

# platform imports
from server import celery_app, db
from server.models.location import Location, LocationExternal
from share.location import LocationExternalSourceEnum, osm_extension_fields

QUERY_TIMEOUT = 2.0
DEFAULT_COUNTRY_CODE = 'KE'
VALID_OSM_ENTRY_TYPES =  ['village', 'suburb', 'address29', 'administrative', 'residential']

logg = logging.getLogger(__file__)

@celery_app.task()
def search_name_from_osm(name, country=DEFAULT_COUNTRY_CODE):
    url = 'https://nominatim.openstreetmap.org/search?format=json&dedupe=1&country={}&q={}'.format(country, name)

    try:
        response = requests.get(url, timeout=QUERY_TIMEOUT)
    except requests.exceptions.Timeout:
        logg.warning('request timeout to openstreetmap; {}:{}'.format(country, name))
        # TODO: re-insert task
        return

    if response.status_code != 200:
        logg.warning('failed request to openstreetmap; {}:{}'.format(country, name))
        return

    response_json = json.loads(response.text)
    logg.debug(response_json)

    # identify a suitable record among those returned
    next_place_id = 0
    for place in response_json:
        if place['type'] in VALID_OSM_ENTRY_TYPES:
            next_place_id = place['place_id']
    if next_place_id == 0:
        logg.debug('no suitable record found in openstreetmap for {}:{}'.format(country, name))
        return

    # get details of place, and recurse parents until top level is reached or found in db
    url = 'https://nominatim.openstreetmap.org/details?format=json&linkedplaces=1&place_id=' 
    locations = []
    cache_index = -1
    while next_place_id != 0:

        r = LocationExternal.get_by_custom(LocationExternalSourceEnum.OSM, 'place_id', next_place_id)
        if len(r) > 0:
            if len(locations) == 0:
                return r[0]
            else:
                cache_index = len(locations)
                break
            
        else:
            try:
                response = requests.get('{}{}'.format(url, next_place_id), timeout=QUERY_TIMEOUT)
            except requests.exceptions.Timeout:
                logg.warning('request timeout to openstreetmap; {}:{}'.format(country, name))
                # TODO: re-insert task
                return

            if response.status_code != 200:
                logg.warning('failed request to openstreetmap; {}:{}'.format(country, name))
                return

            response_json = json.loads(response.text)
            logg.debug(response_json)
            
            next_place_id = response_json['parent_place_id']
            new_location = Location(
                    response_json['names']['name'],
                    response_json['centroid']['coordinates'][0],
                    response_json['centroid']['coordinates'][1]
                    )
            ext_data = {}
            for field in osm_extension_fields:
                ext_data[field] = response_json[field]

        new_location.add_external_data(LocationExternalSourceEnum.OSM, ext_data)
        locations.append(new_location)

                 
    # set hierarchical relations
    for i in range(len(locations)-1):
        locations[i].set_parent(locations[i+1])

    for i in range(cache_index):
        db.session.add(locations[i])

    db.session.commit()
    return locations[0]
