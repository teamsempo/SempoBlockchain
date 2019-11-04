import json, pytest, config, base64


@pytest.mark.parametrize('token_id_generator,amount,status_code', [
    (lambda t: None, None, 400),
    (lambda t: t.id, None, 400),
    (lambda t: t.id, 100, 201)
])
def test_create_poli_payments_link(mocker, test_client, init_database, external_reserve_token,
                                   create_transfer_account_user,
                                   token_id_generator, amount, status_code):
    """
    GIVEN a Flask application
    WHEN '/api/me/poli_payments/' (POST)
    THEN check the response is valid
    """
    # MOCK external API
    ok_response_mock = mocker.MagicMock()
    type(ok_response_mock).status_code = mocker.PropertyMock(return_value=200)
    ok_response_mock.json.return_value = 'https://poli.to/92rQb'

    my_api_client_mock = mocker.MagicMock()
    my_api_client_mock.return_value = ok_response_mock

    # Patch the correct API
    mocker.patch('server.utils.poli_payments.requests.post', my_api_client_mock)

    create_transfer_account_user.is_activated = True
    auth_token = create_transfer_account_user.encode_auth_token()

    token_id = token_id_generator(external_reserve_token)

    response = test_client.post('/api/me/poli_payments/',
                                headers=dict(Authorization=auth_token.decode(), Accept='application/json', ContentType='application/json'),
                                data=json.dumps(dict(token_id=token_id, amount=amount)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code
    if status_code == 201:
        assert create_transfer_account_user.transfer_accounts[0].token.fiat_ramps[0].payment_reference == \
               response.json['data']['payment_reference']


@pytest.mark.parametrize('poli_status,status_code', [
    (None, 400),
    ("Unused", 200),
    ("Completed", 400),  # should fail as once status is requested once, FiatRampStatus is set.
])
def test_check_poli_payments_link_status(mocker, test_client, init_database, external_reserve_token, create_transfer_account_user, poli_status, status_code):
    """
    GIVEN a Flask application
    WHEN '/api/me/poli_payments/' (GET)
    THEN check the response is valid
    """

    # MOCK external API
    ok_response_mock = mocker.MagicMock()
    type(ok_response_mock).status_code = mocker.PropertyMock(return_value=200)
    ok_response_mock.json.return_value = poli_status

    my_api_client_mock = mocker.MagicMock()
    my_api_client_mock.return_value = ok_response_mock

    # Patch the correct API
    mocker.patch('server.utils.poli_payments.requests.get', my_api_client_mock)

    create_transfer_account_user.is_activated = True
    auth_token = create_transfer_account_user.encode_auth_token()

    reference = None
    if poli_status:
        reference = external_reserve_token.fiat_ramps[0].payment_reference

    response = test_client.put('/api/me/poli_payments/',
                                headers=dict(Authorization=auth_token.decode(), Accept='application/json', ContentType='application/json'),
                                data=json.dumps(dict(reference=reference)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code
    if status_code == 200:
        assert response.json.get('data').get('status') == poli_status
