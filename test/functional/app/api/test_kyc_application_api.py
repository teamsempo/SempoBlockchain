import json, pytest
import logging

logg = logging.getLogger(__name__)

@pytest.mark.xfail(reason='test uses wrong parameter for account type against the api, when replaced with correct the test fails')
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
                                data=json.dumps(dict(account_type=type, user_id=user_id)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code

    # Ensure that the posting a duplicate kyc application results in a 400
    response = test_client.post('/api/v1/kyc_application/',
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                data=json.dumps(dict(account_type=type, user_id=user_id)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == 400


@pytest.mark.parametrize('type', [
    ('INDIVIDUAL'),
])
def test_kyc_application_api_status_post(test_client, create_transfer_account_user, complete_admin_auth_token, type):

    logg.debug('create kyc application for user {} type {}'.format(create_transfer_account_user.id, type))
    response = test_client.post('/api/v1/kyc_application/',
        headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
        data=json.dumps(dict(account_type=type, user_id=create_transfer_account_user.id)),
        content_type='application/json', follow_redirects=True)


    logg.debug('response {}'.format(response.data))
    responsedata = response.data.decode('utf-8')
    responsedata_json = json.loads(responsedata)
    kyc_id = responsedata_json['data']['kyc_application']['id']

    logg.debug('using kyc id for status change {}'.format(kyc_id))
    response = test_client.put('/api/v1/kyc_application/{}'.format(kyc_id),
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                #data=json.dumps(dict(type=type, user_id=user_id, override=override, is_mobile=True)),
                                data=json.dumps(dict(account_type=type, user_id=create_transfer_account_user.id, status='VERIFIED')),
                                follow_redirects=True,
                                content_type='application/json',
                                )
    logg.debug('kyc approve response {}'.format(response.data))

    assert response.status_code == 200


@pytest.mark.xfail(reason='due to the limitation that create_transfer_account_user is executed per module only, it is not possible to test with multiple users')
@pytest.mark.parametrize('type', [
    ('BUSINESS')
])
def test_kyc_application_api_status_post_business(test_client, create_transfer_account_user, complete_admin_auth_token, type):

    logg.debug('create kyc application for user {} type {}'.format(create_transfer_account_user.id, type))
    response = test_client.post('/api/v1/kyc_application/',
        headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
        data=json.dumps(dict(account_type=type, user_id=create_transfer_account_user.id)),
        content_type='application/json', follow_redirects=True)


    logg.debug('response {}'.format(response.data))
    responsedata = response.data.decode('utf-8')
    responsedata_json = json.loads(responsedata)
    kyc_id = responsedata_json['data']['kyc_application']['id']

    logg.debug('using kyc id for status change {}'.format(kyc_id))
    response = test_client.put('/api/v1/kyc_application/{}'.format(kyc_id),
                                headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                                #data=json.dumps(dict(type=type, user_id=user_id, override=override, is_mobile=True)),
                                data=json.dumps(dict(account_type=type, user_id=create_transfer_account_user.id, status='VERIFIED')),
                                follow_redirects=True,
                                content_type='application/json',
                                )
    logg.debug('kyc approve response {}'.format(response.data))

    assert response.status_code == 200

