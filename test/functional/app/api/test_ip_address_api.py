"""
This file (test_ip_address_api.py) contains the functional tests for the api blueprint.

These tests use POSTs to different URLs to check for the proper behavior
of the auth blueprint.
"""
import json, pytest, config, base64


@pytest.mark.parametrize('ip_address_id,country,status_code', [
    (1, 'AU', 201),
    (None, None, 400),
    (123123, None, 404)
])
def test_ip_address_api(test_client, create_ip_address, ip_address_id,country,status_code):
    """
    GIVEN a Flask application
    WHEN the '/api/ip_address_location/' page is requested (POST)
    THEN check the response is valid
    """

    basic_auth = 'Basic ' + base64.b64encode(bytes(config.BASIC_AUTH_USERNAME + ":" + config.BASIC_AUTH_PASSWORD, 'ascii')).decode('ascii')

    response = test_client.post('/api/ip_address_location/',
                                headers=dict(Authorization=basic_auth, Accept='application/json'),
                                data=json.dumps(dict(ip_address_id=ip_address_id, country=country)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code
