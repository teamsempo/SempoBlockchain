"""
This file (test_transfer_usage_api.py) contains the functional tests for the transfer_usage_blueprint.

These tests use GETs and POSTs to different URLs to check for the proper behavior
of the transfer_usage_blueprint.
"""
import json, pytest


@pytest.mark.parametrize('name,icon,translations,status_code', [
    ('Food', 'food-apple', dict(en='Food', fr='aliments'), 201),
    (None, None, None, 400),
    ('Food', 'bananaaaas', None, 400)
])
def test_transfer_usage_api(test_client, authed_sempo_admin_user,name,icon,translations,status_code):
    """
    GIVEN a Flask application
    WHEN the '/api/transfer_usage/' page is requested (POST)
    THEN check the response is valid
    """
    authed_sempo_admin_user.is_activated = True
    authed_sempo_admin_user.TFA_enabled = True
    authed_sempo_admin_user.set_held_role('ADMIN', 'admin')
    auth_token = authed_sempo_admin_user.encode_auth_token().decode()
    tfa_token = authed_sempo_admin_user.encode_TFA_token(9999).decode()

    response = test_client.post('/api/transfer_usage/',
                                headers=dict(Authorization=auth_token + '|' + tfa_token, Accept='application/json'),
                                data=json.dumps(dict(name=name, icon=icon, translations=translations)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code
