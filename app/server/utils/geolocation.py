import googlemaps
from flask import current_app
from server import db
from server.models.models import TransferAccount

gmaps = googlemaps.Client(key=current_app.config['GOOGLE_GEOCODE_KEY'])

def save_beneficiary_latlng(address, beneficiary_id):

    geocode_result = gmaps.geocode(address)

    try:
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']

        print('lat: ' + str(lat) + ' lng: ' + str(lng))


        beneficiary = TransferAccount.query.get(beneficiary_id)


        beneficiary.lat = lat
        beneficiary.lng = lng

        db.session.commit()

        print('saved location')

        return {'message': 'success', 'lat': lat, 'lng': lng}

    except IndexError:

        return {'message': 'Could not find address'}

