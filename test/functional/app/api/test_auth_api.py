"""
This file (test_auth_api.py) contains the functional tests for the auth blueprint.

These tests use GETs and POSTs to different URLs to check for the proper behavior
of the auth blueprint.
"""
from time import sleep
from datetime import datetime
import pytest, json, config, base64
import pyotp

from server.utils.auth import get_complete_auth_token

# todo- permissions api, reset password, request reset password

@pytest.mark.parametrize("username,password,status_code", [
    (config.INTERNAL_AUTH_USERNAME, config.INTERNAL_AUTH_PASSWORD, 201),
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

@pytest.mark.parametrize("activation_token", [
    "alsdfjkadsljflk",
    None,
])
def test_invalid_activate_api(test_client, new_sempo_admin_user, activation_token):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/activate/' api is posted to (POST)
    THEN check the response is invalid when activation_token is incorrect or None
    """
    assert not new_sempo_admin_user.is_activated
    response = test_client.post('/api/auth/activate/',
                                data=json.dumps(dict(activation_token=activation_token)),
                                content_type='application/json', follow_redirects=True)
    assert response.status_code == 401
    assert not new_sempo_admin_user.is_activated

def test_valid_activate_api(test_client, new_sempo_admin_user):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/activate/' api is posted to (POST)
    THEN check the response is valid when correct activation_token
    """
    assert not new_sempo_admin_user.is_activated
    activation_token = new_sempo_admin_user.encode_single_use_JWS('A')
    response = test_client.post('/api/auth/activate/',
                                data=json.dumps(dict(activation_token=activation_token)),
                                content_type='application/json', follow_redirects=True)
    assert response.status_code == 201
    assert new_sempo_admin_user.is_activated


def test_get_tfa_url(test_client, activated_sempo_admin_user):
    """
    GIVEN a Flask Application
    WHEN '/api/auth/tfa/' is requested (GET)
    THEN check tfa url is valid
    """
    activated_sempo_admin_user.set_held_role('ADMIN', 'subadmin')
    auth_token = activated_sempo_admin_user.encode_auth_token().decode()
    response = test_client.get('/api/auth/tfa/',
                               headers=dict(Authorization=auth_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 200
    assert response.json['data']['tfa_url'] == activated_sempo_admin_user.tfa_url
    activated_sempo_admin_user.set_held_role('ADMIN', 'sempoadmin')

@pytest.mark.parametrize("otp_generator, status_code", [
    (lambda f: f.now(), 200),
    (lambda f: f.at(datetime.now(), -1), 200),
    (lambda f: 'not a numeric str', 400),
    (lambda f: 123456, 400),
    (lambda f: '1234567', 400),
    (lambda f: f.at(datetime.now(), -4), 400),
    (lambda f: '1230924579324', 400),
])
def test_request_tfa_token(test_client, authed_sempo_admin_user, otp_generator, status_code):
    """
    GIVEN a Flask Application
    WHEN '/api/auth/tfa/' is requested (POST)
    THEN check a tfa token is only returned when OTP is valid
    """

    auth_token = authed_sempo_admin_user.encode_auth_token().decode()

    tfa_url = authed_sempo_admin_user.tfa_url
    tfa_secret = tfa_url.split("secret=")[1].split('&')[0]
    func = pyotp.TOTP(tfa_secret)
    otp = otp_generator(func)

    otp_expiry_interval = 1
    response = test_client.post('/api/auth/tfa/',
                                headers=dict(Authorization=auth_token, Accept='application/json'),
                                json=dict(
                                    otp=otp,
                                    otp_expiry_interval=otp_expiry_interval
                                ),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code

@pytest.mark.parametrize("email,password,status_code", [
    ("tristan@sempo.ai", "TestPassword", 200),
    ("tristan@sempo.ai", "IncorrectTestPassword", 401),
    ("tristan+123@sempo.ai", "IncorrectTestPassword", 401),
])
def test_request_api_token(test_client, authed_sempo_admin_user, email, password, status_code):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/request_api_token/' api is posted to (POST)
    THEN check response as a admin user (email, password)
    """

    tfa_token = authed_sempo_admin_user.encode_TFA_token(9999).decode()
    response = test_client.post('/api/auth/request_api_token/',
                                data=json.dumps(dict(email=email, password=password, tfa_token=tfa_token)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code

@pytest.mark.parametrize("message,is_activated,status_code", [
    ('Please set your pin.', False, 200),
    ('Successfully logged in.', True, 200),
])
def test_request_api_token_phone_success(test_client, create_transfer_account_user, message, is_activated, status_code):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/request_api_token/' api is posted to (POST) as a mobile app user (phone, pin)
    THEN check a valid response as a mobile app user (phone, pin)
    """

    create_transfer_account_user.is_activated = is_activated
    one_time_code = create_transfer_account_user.one_time_code
    create_transfer_account_user.hash_password(one_time_code)  # set the one time code as password for easy check

    response = test_client.post('/api/auth/request_api_token/',
                                data=json.dumps(dict(phone=create_transfer_account_user.phone, password=one_time_code)),
                                content_type='application/json', follow_redirects=True)
    assert response.status_code == status_code
    assert response.json['message'] == message


@pytest.mark.parametrize("phone,message,is_activated,status_code", [
    (None, 'No username supplied', False, 401),
    ('12312111111111113123', 'Invalid Phone Number: (4) The string supplied is too long to be a phone number.',
     True, 401)
])
def test_request_api_token_phone_fail(test_client, create_transfer_account_user, phone, message, is_activated, status_code):
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
    assert response.json['message'] == message


def test_logout_api(test_client, authed_sempo_admin_user):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/logout/' api is posted to (POST)
    THEN check response is 200 and auth_token is added to blacklist
    """
    from server.models.blacklist_token import BlacklistToken
    authed_sempo_admin_user.is_activated = True
    auth_token = authed_sempo_admin_user.encode_auth_token().decode()
    response = test_client.post('/api/auth/logout/',
                               headers=dict(Authorization=auth_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 200
    assert BlacklistToken.check_blacklist(auth_token) is True

    @pytest.mark.parametrize("email, tier, status_code", [
        ("test@test.com","admin",201),
        ("tristan@sempo.ai","admin", 403),
    ])
    def test_add_user_to_whitelist(test_client, authed_sempo_admin_user, email, tier, status_code):
        """
        GIVEN a Flask application
        WHEN the '/api/auth/permissions/' api is posted to (POST)
        THEN check the response
        """

        auth_token = authed_sempo_admin_user.encode_auth_token().decode()
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
#     from server.models.user import User
#     register_response = test_client.post('/api/auth/register/',
#                                 data=json.dumps(dict(email=email, password='TestPassword')),
#                                 content_type='application/json', follow_redirects=True)
#     assert register_response.status_code == status_code

@pytest.mark.parametrize("tier,status_code", [
    ('admin', 401),
    ('superadmin', 200),
])
def test_blockchain_key_api(test_client, authed_sempo_admin_user, tier, status_code):
    """
    GIVEN a Flask application
    WHEN '/api/auth/blockchain/' is requested (GET)
    THEN check the response is only returned for is_superadmin
    """

    authed_sempo_admin_user.set_held_role('ADMIN',tier)
    response = test_client.get('/api/auth/blockchain/',
                               headers=dict(
                                   Authorization=get_complete_auth_token(authed_sempo_admin_user),
                                   Accept='application/json'
                               ),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == status_code


def test_get_permissions_api(test_client, complete_admin_auth_token):
    """
    GIVEN a Flask application
    WHEN '/api/auth/permissions/' is requested (GET)
    THEN check a list of admins is returned
    """
    response = test_client.get('/api/auth/permissions/',
                               headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 200
    assert response.json['admin_list'] is not None


def get_admin_default_org_id(admin_user):
    return admin_user.default_organisation_id


@pytest.mark.parametrize("creator_tier, email, invitee_tier, organisation_id_selector, response_code", [
    ('admin', 'foo@acme.com', 'admin', get_admin_default_org_id, 401),
    ('sempoadmin', 'foo@acme.com', 'admin', lambda o: 12332, 404),
    ('sempoadmin',  None, 'admin', get_admin_default_org_id, 400),
    ('sempoadmin', 'foo@acme.com', None, get_admin_default_org_id, 400),
    ('sempoadmin', 'foo@acme.com', 'admin', get_admin_default_org_id, 200),
    ('sempoadmin', 'foo@acme.com', 'admin', get_admin_default_org_id, 400),
])

def test_create_permissions_api(test_client, authed_sempo_admin_user,
                                creator_tier, email, invitee_tier, organisation_id_selector, response_code):
    """
    GIVEN a Flask application
    WHEN A new email is POSTED to '/api/auth/permissions/'
    THEN check it is added successfully
    """
    authed_sempo_admin_user.set_held_role('ADMIN', creator_tier)

    organisation_id = organisation_id_selector(authed_sempo_admin_user)

    response = test_client.post('/api/auth/permissions/',
                                headers=dict(
                                    Authorization=get_complete_auth_token(authed_sempo_admin_user),
                                    Accept='application/json'
                                ),
                                json={'email': email, 'tier': invitee_tier, 'organisation_id': organisation_id})

    assert response.status_code == response_code


def test_get_kobo_credentials_api(test_client, authed_sempo_admin_user):
    """
    GIVEN a Flask Application
    WHEN '/api/auth/kobo/' is requested (GET)
    THEN check kobo details username and password are returned
    """
    authed_sempo_admin_user.is_activated = True
    authed_sempo_admin_user.TFA_enabled = True
    authed_sempo_admin_user.set_held_role('ADMIN', 'admin')
    auth_token = authed_sempo_admin_user.encode_auth_token().decode()
    tfa_token = authed_sempo_admin_user.encode_TFA_token(9999).decode()
    response = test_client.get('/api/auth/kobo/',
                               headers=dict(Authorization=auth_token + '|' + tfa_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 200
    assert response.json['username'] == config.EXTERNAL_AUTH_USERNAME
    assert response.json['password'] == config.EXTERNAL_AUTH_PASSWORD


def test_logout_api(test_client, authed_sempo_admin_user):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/logout/' api is posted to (POST)
    THEN check response is 200 and auth_token is added to blacklist
    """
    from server.models.blacklist_token import BlacklistToken
    authed_sempo_admin_user.is_activated = True
    auth_token = authed_sempo_admin_user.encode_auth_token().decode()
    response = test_client.post('/api/auth/logout/',
                               headers=dict(Authorization=auth_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 200
    assert BlacklistToken.check_blacklist(auth_token) is True

    # This is here to stop tokens having the same timestamp dying
    sleep(1)


def test_reset_password_valid_token(test_client, authed_sempo_admin_user):
    """
    GIVEN a Flask application
    WHEN a valid the password reset token is POSTED to '/api/auth/reset_password/'
    THEN check response is 200 and check if password changed
    """
    import bcrypt

    # Explicitly test None case since database migration can result in None instead of []
    authed_sempo_admin_user.password_reset_tokens = None

    password_reset_token = authed_sempo_admin_user.encode_single_use_JWS('R')
    authed_sempo_admin_user.save_password_reset_token(password_reset_token)
    password = 'NewTestPassword'

    response = test_client.post('/api/auth/reset_password/',
                                data=json.dumps(dict(new_password=password, reset_password_token=password_reset_token)),
                                content_type='application/json', follow_redirects=True)

    assert bcrypt.checkpw(
        password.encode(), authed_sempo_admin_user.password_hash.encode())
    assert authed_sempo_admin_user.password_reset_tokens == []
    assert response.status_code == 200


def test_reset_password_used_token(test_client, authed_sempo_admin_user):
    # Explicitly test None case since database migration can result in None instead of []
    """
    GIVEN a Flask application
    WHEN a used the password reset token is POSTED to '/api/auth/reset_password/'
    THEN check response is 401
    """

    authed_sempo_admin_user.password_reset_tokens = None

    password_reset_token = authed_sempo_admin_user.encode_single_use_JWS('R')
    authed_sempo_admin_user.save_password_reset_token(password_reset_token)
    password = 'NewTestPassword'


    # Use password for the first time
    test_client.post('/api/auth/reset_password/',
                            data=json.dumps(
                            dict(new_password=password, reset_password_token=password_reset_token)),
                            content_type='application/json', follow_redirects=True)

    # Use password for the second time
    response = test_client.post('/api/auth/reset_password/',
                                data=json.dumps(
                                dict(new_password=password, reset_password_token=password_reset_token)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == 401
    assert response.json['message'] == 'Token already used'
