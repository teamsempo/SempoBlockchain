"""
This file (test_auth_api.py) contains the functional tests for the auth blueprint.

These tests use GETs and POSTs to different URLs to check for the proper behavior
of the auth blueprint.
"""
import pytest, json, config, base64

from server import db


# todo- permissions api, reset password, request reset password


@pytest.mark.parametrize("username,password,status_code", [
    (config.BASIC_AUTH_USERNAME, config.BASIC_AUTH_PASSWORD, 201),
    ("fake_username", "fake_password", 401)
])
def test_basic_auth(test_client, username, password, status_code):
    """
    GIVEN a Flask Application
    WHEN the '/api/auth/check_basic_auth/' api is requested (GET)
    THEN check the response is valid
    """

    basic_auth = 'Basic ' + base64.b64encode(
        bytes(username + ":" + password, 'ascii')).decode('ascii')

    response = test_client.get('/api/auth/check_basic_auth/',
                               headers=dict(Authorization=basic_auth, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code


@pytest.mark.parametrize("email,password,status_code", [
    ("tristan@sempo.ai", "TestPassword", 200),
    ("tristan@sempo.ai", "IncorrectTestPassword", 401),
    ("tristan+123@sempo.ai", "IncorrectTestPassword", 401),
])
def test_request_api_token(test_client, create_sempo_admin_user, email, password, status_code):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/request_api_token/' api is posted to (POST)
    THEN check response as a admin user (email, password)
    """

    response = test_client.post('/api/auth/request_api_token/',
                                data=json.dumps(dict(email=email, password=password)),
                                content_type='application/json', follow_redirects=True)
    assert response.status_code == status_code


@pytest.mark.parametrize("phone,message,is_activated,status_code", [
    (None, 'No username supplied', False, 401),
    ('0400000000', 'Please set your pin.', False, 200),
    ('0400000000', 'Successfully logged in.', True, 200),
    ('12312111111111113123', 'Invalid Phone Number: (4) The string supplied is too long to be a phone number.',
     True, 401)
])
def test_request_api_token_phone(test_client, create_transfer_account_user, phone, message, is_activated, status_code):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/request_api_token/' api is posted to (POST) as a mobile app user (phone, pin)
    THEN check a valid response as a mobile app user (phone, pin)
    """

    create_transfer_account_user.is_activated = is_activated
    one_time_code = create_transfer_account_user.one_time_code
    create_transfer_account_user.hash_password(one_time_code)  # set the one time code as password for easy check

    response = test_client.post('/api/auth/request_api_token/',
                                data=json.dumps(dict(phone=phone, password=one_time_code)),
                                content_type='application/json', follow_redirects=True)
    assert response.status_code == status_code
    assert json.loads(response.data)['message'] == message


def test_logout_api(test_client, create_sempo_admin_user):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/logout/' api is posted to (POST)
    THEN check response is 200 and auth_token is added to blacklist
    """
    from server.models import BlacklistToken
    create_sempo_admin_user.is_activated = True
    auth_token = create_sempo_admin_user.encode_auth_token().decode()
    response = test_client.post('/api/auth/logout/',
                               headers=dict(Authorization=auth_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 200
    assert BlacklistToken.check_blacklist(auth_token) is True

    @pytest.mark.parametrize("email, tier, status_code", [
        ("test@test.com","admin",201),
        ("tristan@sempo.ai","admin", 403),
    ])
    def test_add_user_to_whitelist(test_client, create_sempo_admin_user, email, tier, status_code):
        """
        GIVEN a Flask application
        WHEN the '/api/auth/permissions/' api is posted to (POST)
        THEN check the response
        """

        auth_token = create_sempo_admin_user.encode_auth_token().decode()
        register_response = test_client.post('/api/auth/permissions/',
                                             headers=dict(Authorization=auth_token, Accept='application/json'),
                                             data=json.dumps(dict(email=email, tier=tier)),
                                             content_type='application/json', follow_redirects=True)
        assert register_response.status_code == status_code


# todo- need to mock boto3 SES api so i'm not bombarded with emails
# @pytest.mark.parametrize("email,status_code", [
#     ("tristan+1@sempo.ai", 201),
#     ("tristan", 403),
# ])
# def test_register_and_activate_api(test_client, init_database, email, status_code):
#     """
#     GIVEN a Flask application
#     WHEN the '/api/auth/register/' api is posted to (POST)
#     THEN check the response
#     """
#     from server.models import User
#     register_response = test_client.post('/api/auth/register/',
#                                 data=json.dumps(dict(email=email, password='TestPassword')),
#                                 content_type='application/json', follow_redirects=True)
#     assert register_response.status_code == status_code


def test_valid_activate_api(test_client, create_sempo_admin_user):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/activate/' api is posted to (POST)
    THEN check the response is valid when correct activation_token
    """
    assert not create_sempo_admin_user.is_activated
    activation_token = create_sempo_admin_user.encode_single_use_JWS('A')
    response = test_client.post('/api/auth/activate/',
                                data=json.dumps(dict(activation_token=activation_token)), 
                                content_type='application/json', follow_redirects=True)
    assert response.status_code == 201
    assert create_sempo_admin_user.is_activated


@pytest.mark.parametrize("activation_token", [
    "alsdfjkadsljflk",
    None,
])
def test_invalid_activate_api(test_client, create_sempo_admin_user, activation_token):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/activate/' api is posted to (POST)
    THEN check the response is invalid when activation_token is incorrect or None
    """
    assert not create_sempo_admin_user.is_activated
    response = test_client.post('/api/auth/activate/',
                                data=json.dumps(dict(activation_token=activation_token)),
                                content_type='application/json', follow_redirects=True)
    assert response.status_code == 401
    assert not create_sempo_admin_user.is_activated


@pytest.mark.parametrize("tier,status_code", [
    ('admin', 401),
    ('superadmin', 200),
])
def test_blockchain_key_api(test_client, create_sempo_admin_user, tier, status_code):
    """
    GIVEN a Flask application
    WHEN '/api/auth/blockchain/' is requested (GET)
    THEN check the response is only returned for is_superadmin
    """

    create_sempo_admin_user.is_activated = True
    create_sempo_admin_user.TFA_enabled = True
    create_sempo_admin_user.set_admin_role_using_tier_string(tier)
    auth_token = create_sempo_admin_user.encode_auth_token().decode()
    tfa_token = create_sempo_admin_user.encode_TFA_token(9999).decode()
    response = test_client.get('/api/auth/blockchain/',
                               headers=dict(Authorization=auth_token + '|' + tfa_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == status_code


def test_get_permissions_api(test_client, create_sempo_admin_user):
    """
    GIVEN a Flask application
    WHEN '/api/auth/permissions/' is requested (GET)
    THEN check a list of admins is returned
    """
    create_sempo_admin_user.is_activated = True
    create_sempo_admin_user.TFA_enabled = True
    create_sempo_admin_user.set_admin_role_using_tier_string('admin')
    auth_token = create_sempo_admin_user.encode_auth_token().decode()
    tfa_token = create_sempo_admin_user.encode_TFA_token(9999).decode()
    response = test_client.get('/api/auth/permissions/',
                               headers=dict(Authorization=auth_token + '|' + tfa_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 200
    assert json.loads(response.data)['admin_list'] is not None


def test_get_kobo_credentials_api(test_client, create_sempo_admin_user):
    """
    GIVEN a Flask Application
    WHEN '/api/auth/kobo/' is requested (GET)
    THEN check kobo details username and password are returned
    """
    create_sempo_admin_user.is_activated = True
    create_sempo_admin_user.TFA_enabled = True
    create_sempo_admin_user.set_admin_role_using_tier_string('admin')
    auth_token = create_sempo_admin_user.encode_auth_token().decode()
    tfa_token = create_sempo_admin_user.encode_TFA_token(9999).decode()
    response = test_client.get('/api/auth/kobo/',
                               headers=dict(Authorization=auth_token + '|' + tfa_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 200
    assert json.loads(response.data)['username'] == config.KOBO_AUTH_USERNAME
    assert json.loads(response.data)['password'] == config.KOBO_AUTH_PASSWORD


def test_get_tfa_url(test_client, create_sempo_admin_user):
    """
    GIVEN a Flask Application
    WHEN '/api/auth/tfa/' is requested (GET)
    THEN check tfa url is valid
    """
    create_sempo_admin_user.is_activated = True
    create_sempo_admin_user.set_admin_role_using_tier_string('subadmin')
    auth_token = create_sempo_admin_user.encode_auth_token().decode()
    response = test_client.get('/api/auth/tfa/',
                               headers=dict(Authorization=auth_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 200
    assert json.loads(response.data)['data']['tfa_url'] == create_sempo_admin_user.tfa_url


@pytest.mark.parametrize("otp,status_code", [
    (None, 200),
    ('1230924579324', 400),
])
def test_request_tfa_token(test_client, create_sempo_admin_user, otp, status_code):
    """
    GIVEN a Flask Application
    WHEN '/api/auth/tfa/' is requested (POST)
    THEN check a tfa token is only returned when OTP is valid
    """
    import pyotp
    create_sempo_admin_user.is_activated = True
    create_sempo_admin_user.tfa_url  # this needs to be called to generate a tfa secret and save it to user object
    auth_token = create_sempo_admin_user.encode_auth_token().decode()

    if otp is None:
        otp = pyotp.TOTP(create_sempo_admin_user._get_TFA_secret()).now()

    otp_expiry_interval = 1
    response = test_client.post('/api/auth/tfa/',
                                headers=dict(Authorization=auth_token, Accept='application/json'),
                                data=json.dumps(dict(otp=otp, otp_expiry_interval=otp_expiry_interval)),
                                content_type='application/json', follow_redirects=True)
    assert response.status_code == status_code
