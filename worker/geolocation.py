import googlemaps

import config

gmaps = googlemaps.Client(key=config.GOOGLE_GEOCODE_KEY)

def calculate_address_latlng(address):

    if address is not None:

        geocode_result = gmaps.geocode(address)

        try:
            lat = geocode_result[0]['geometry']['location']['lat']
            lng = geocode_result[0]['geometry']['location']['lng']

            return {'status': 'success', 'lat': lat, 'lng': lng}

        except IndexError:

            return {'status': 'failure', 'message': 'Could not find address'}

    else:

        return {'status': 'failure', 'message': 'No Address'}


def parse_geo_task(task):
    user_id = task.get('user_id')
    address = task.get('address')

    if not address:
        return {'status': 'Fail'}

    response = calculate_address_latlng(address)

    response['user_id'] = user_id

    return response