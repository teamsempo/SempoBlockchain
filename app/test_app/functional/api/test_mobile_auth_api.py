import json
from faker.providers import phone_number
from faker import Faker
from functools import partial

fake = Faker()
fake.add_provider(phone_number)
phone = partial(fake.msisdn)


def test_request_api_token_golden_path_success(
        test_client,
        mock_sms_apis,
        initialised_blockchain_network,
        create_transfer_account_user
):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/request_api_token/' api is posted to (POST) as a mobile app user who IS registered
    THEN check valid responses as a user wallet is created, provides OTP code and sets a PIN
    """

    user_phone = create_transfer_account_user.phone

    create_response = test_client.post('/api/v1/auth/request_api_token/',
                                       data=json.dumps(dict(phone=user_phone)),
                                       content_type='application/json', follow_redirects=True)

    assert create_response.status_code == 200
    assert create_response.json['message'] == 'Please verify phone number.'

    code = create_transfer_account_user.one_time_code

    failed_otp_response = test_client.post('/api/v1/auth/request_api_token/',
                                          data=json.dumps(dict(phone=user_phone, password='12344')),
                                          content_type='application/json', follow_redirects=True)

    assert failed_otp_response.status_code == 200
    assert failed_otp_response.json['message'] == 'Please verify phone number.'

    otp_response = test_client.post('/api/v1/auth/request_api_token/',
                                    data=json.dumps(
                                        dict(phone=user_phone, password=code)),
                                    content_type='application/json', follow_redirects=True)

    assert otp_response.status_code == 200
    assert otp_response.json['message'] == 'Please set your pin.'

    set_pin_response = test_client.post('/api/v1/auth/reset_password/',
                                        data=json.dumps(
                                            dict(phone=user_phone, new_password='1234', one_time_code=code)),
                                        content_type='application/json', follow_redirects=True)

    assert set_pin_response.status_code == 200
    assert set_pin_response.json['message'] == 'Successfully set pin'