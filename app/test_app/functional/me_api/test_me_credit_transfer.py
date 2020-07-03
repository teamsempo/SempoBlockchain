
def test_get_me_credit_transfer_api(test_client, create_credit_transfer, create_transfer_account_user):
    """
    GIVEN a Flask application
    WHEN '/api/me/credit_transfer/' is requested (GET)
    THEN check a list of credit transfers is returned
    """
    create_transfer_account_user.is_activated = True
    auth_token = create_transfer_account_user.encode_auth_token()

    response = test_client.get('/api/v1/me/credit_transfer/',
                               headers=dict(Authorization=auth_token.decode(), Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 201
    assert response.json['data']['credit_transfers'][0]['id'] is create_credit_transfer.id
