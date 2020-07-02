import json
from faker.providers import phone_number
from faker import Faker
from functools import partial

fake = Faker()
fake.add_provider(phone_number)
phone = partial(fake.msisdn)


def test_request_api_token_golden_path_success(test_client, mock_sms_apis, initialised_blockchain_network):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/request_api_token/' api is posted to (POST) as a mobile app user who ISN'T registered
    THEN check valid responses as a user wallet is created, provides OTP code and sets a PIN
    """

    user_phone = phone()

    create_response = test_client.post('/api/v1/auth/request_api_token/',
                                       data=json.dumps(dict(phone=user_phone)),
                                       content_type='application/json', follow_redirects=True)

    assert create_response.status_code == 200
    assert create_response.json['message'] == 'User Created. Please verify phone number.'

    messages = mock_sms_apis

    assert len(messages) == 3  # Messages: Onboarding, Terms, Verification code
    code = messages[2]['message'][-4:]

    otp_response = test_client.post('/api/v1/auth/request_api_token/',
                                    data=json.dumps(dict(phone=user_phone, password=code)),
                                    content_type='application/json', follow_redirects=True)

    assert otp_response.status_code == 200
    assert otp_response.json['message'] == 'Please set your pin.'

    set_pin_response = test_client.post('/api/v1/auth/reset_password/',
                                        data=json.dumps(
                                            dict(phone=user_phone, new_password='1234', one_time_code=code)),
                                        content_type='application/json', follow_redirects=True)

    assert set_pin_response.status_code == 200
    assert set_pin_response.json['message'] == 'Successfully set pin'


def test_request_api_token_golden_path_fail_otp(test_client, mock_sms_apis, initialised_blockchain_network):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/request_api_token/' api is posted to (POST) as a mobile app user who ISN'T registered
    THEN check valid responses as a user wallet is created, provides OTP code and sets a PIN
    """

    user_phone = phone()

    create_response = test_client.post('/api/v1/auth/request_api_token/',
                                       data=json.dumps(dict(phone=user_phone)),
                                       content_type='application/json', follow_redirects=True)

    assert create_response.status_code == 200
    assert create_response.json['message'] == 'User Created. Please verify phone number.'

    messages = mock_sms_apis

    assert len(messages) == 3  # Messages: Onboarding, Terms, Verification code

    first_otp_response = test_client.post('/api/v1/auth/request_api_token/',
                                          data=json.dumps(dict(phone=user_phone, password='12344')),
                                          content_type='application/json', follow_redirects=True)

    assert first_otp_response.status_code == 200
    assert first_otp_response.json['message'] == 'Please verify phone number.'

    assert len(messages) == 4  # Messages: Onboarding, Terms, Verification code, Second Verification Code
    code = messages[3]['message'][-4:]

    second_otp_response = test_client.post('/api/v1/auth/request_api_token/',
                                           data=json.dumps(dict(phone=user_phone, password=code)),
                                           content_type='application/json', follow_redirects=True)

    assert second_otp_response.status_code == 200
    assert second_otp_response.json['message'] == 'Please set your pin.'

    set_pin_response = test_client.post('/api/v1/auth/reset_password/',
                                        data=json.dumps(
                                            dict(phone=user_phone, new_password='1234', one_time_code=code)),
                                        content_type='application/json', follow_redirects=True)

    assert set_pin_response.status_code == 200
    assert set_pin_response.json['message'] == 'Successfully set pin'
