import json, pytest


@pytest.mark.parametrize('type,user_id,status_code', [
    ('INDIVIDUAL', 1, 201),
    ('INDIVIDUAL', None, 400),
    ('BUSINESS', 1, 400),
])
def test_kyc_application_api_post(test_client, complete_admin_auth_token, type, user_id, status_code):
    """
    GIVEN a Flask application
    WHEN the '/api/kyc_application/' page is requested (POST)
    THEN check the response is expected
    """

    response = test_client.post('/api/v1/kyc_application/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps(dict(type=type, user_id=user_id)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code

    # Ensure that the posting a duplicate kyc application results in a 400
    response = test_client.post('/api/v1/kyc_application/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps(dict(type=type, user_id=user_id)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == 400

