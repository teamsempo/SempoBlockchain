"""
This file (test_transfer_usage_api.py) contains the functional tests for the transfer_usage_blueprint.

These tests use GETs and POSTs to different URLs to check for the proper behavior
of the transfer_usage_blueprint.
"""
import json, pytest
from server.utils.auth import get_complete_auth_token


@pytest.mark.parametrize('name,icon,translations,status_code', [
    ('Food', 'food-apple', dict(en='Food', fr='aliments'), 201),
    (None, None, None, 400),
    ('Food', 'bananaaaas', None, 400)
])
def test_transfer_usage_api(test_client, complete_admin_auth_token, name, icon, translations,status_code):
    """
    GIVEN a Flask application
    WHEN the '/api/transfer_usage/' page is requested (POST)
    THEN check the response is valid
    """

    response = test_client.post('/api/v1/transfer_usage/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps(dict(name=name, icon=icon, translations=translations)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code

    # Ensure that the posting a duplicate transfer ussage results in a 400
    response = test_client.post('/api/v1/transfer_usage/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps(dict(name=name, icon=icon, translations=translations)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == 400


def test_transfer_usage_api_get(test_client, complete_admin_auth_token):
    """
    GIVEN a Flask application
    WHEN the '/api/transfer_usage/' page is requested (GET)
    THEN check the response has status 200 and a list
    """

    response = test_client.get('/api/v1/transfer_usage/',
                               headers=dict(
                                   Authorization=complete_admin_auth_token, Accept='application/json'),
                               follow_redirects=True)

    assert response.status_code == 200
    assert isinstance(response.json['data']['transfer_usages'], list)
