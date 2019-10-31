
def test_me_api(test_client, create_transfer_account_user):
    """
    GIVEN a Flask application
    WHEN the '/api/me/' page is requested (GET)
    THEN check the response is valid
    """
    create_transfer_account_user.is_activated = True
    auth_token = create_transfer_account_user.encode_auth_token()

    response = test_client.get('/api/me/',
                               headers=dict(Authorization=auth_token.decode(), Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 201
    assert response.json['data']['user'] is not None
