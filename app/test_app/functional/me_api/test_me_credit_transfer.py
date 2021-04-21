import pytest, json, base64, config


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


def test_invalid_create_me_credit_transfer_api(
        test_client,
        create_transfer_account_user,
        create_transfer_account_user_2
):
    """
    Tests that a user can only send a transfer from an account they own
    """

    auth_token = create_transfer_account_user.encode_auth_token()

    ta1 = create_transfer_account_user.default_transfer_account
    ta2 = create_transfer_account_user_2.default_transfer_account

    ta1.is_approved = True
    ta2.is_approved = True

    ta1.set_balance_offset(1000)
    ta2.set_balance_offset(1000)


    response = test_client.post(
        '/api/v1/me/credit_transfer/',
        headers=dict(
            Authorization=auth_token.decode(),
            Accept='application/json'
        ),
        data=json.dumps(dict(
            is_sending=True,
            transfer_amount=10,
            my_transfer_account_id=ta2.id,
            transfer_account_id=ta1.id
        )),
        content_type='application/json', follow_redirects=True)

    assert response.status_code == 401
