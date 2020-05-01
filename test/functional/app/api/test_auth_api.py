"""
This file (test_auth_api.py) contains the functional tests for the auth blueprint.

These tests use GETs and POSTs to different URLs to check for the proper behavior
of the auth blueprint.
"""
from time import sleep
from datetime import datetime
import pytest, json, config, base64
import pyotp
from cryptography.fernet import Fernet

from server.models.organisation import Organisation
from server.utils.auth import get_complete_auth_token


def interal_auth_username():
    return config.INTERNAL_AUTH_USERNAME


def interal_auth_password():
    return config.INTERNAL_AUTH_PASSWORD


def external_auth_username():
    org = Organisation.query.first()
    return org.external_auth_username


def external_auth_password():
    org = Organisation.query.first()
    return org.external_auth_password


def fake_username():
    return 'FakeUser'


def fake_password():
    return 'FakePass'


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
    response = test_client.post('/api/v1/auth/activate/',
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
    response = test_client.post('/api/v1/auth/activate/',
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
    response = test_client.get('/api/v1/auth/tfa/',
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
    response = test_client.post('/api/v1/auth/tfa/',
                                headers=dict(Authorization=auth_token, Accept='application/json'),
                                json=dict(
                                    otp=otp,
                                    otp_expiry_interval=otp_expiry_interval
                                ),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code

@pytest.mark.parametrize("email,password,status_code", [
    ("tristan@withsempo.com", "TestPassword", 200),
    ("tristan@withsempo.com", "IncorrectTestPassword", 401),
    ("tristan+123@withsempo.com", "IncorrectTestPassword", 401),
])
def test_request_api_token(test_client, authed_sempo_admin_user, email, password, status_code):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/request_api_token/' api is posted to (POST)
    THEN check response as a admin user (email, password)
    """

    tfa_token = authed_sempo_admin_user.encode_TFA_token(9999).decode()
    response = test_client.post('/api/v1/auth/request_api_token/',
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

    response = test_client.post('/api/v1/auth/request_api_token/',
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

    response = test_client.post('/api/v1/auth/request_api_token/',
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
    response = test_client.post('/api/v1/auth/logout/',
                               headers=dict(Authorization=auth_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 200
    assert BlacklistToken.check_blacklist(auth_token) is True

    @pytest.mark.parametrize("email, tier, status_code", [
        ("test@test.com","admin",201),
        ("tristan@withsempo.com","admin", 403),
    ])
    def test_add_user_to_whitelist(test_client, authed_sempo_admin_user, email, tier, status_code):
        """
        GIVEN a Flask application
        WHEN the '/api/auth/permissions/' api is posted to (POST)
        THEN check the response
        """

        auth_token = authed_sempo_admin_user.encode_auth_token().decode()
        register_response = test_client.post('/api/v1/auth/permissions/',
                                             headers=dict(Authorization=auth_token, Accept='application/json'),
                                             data=json.dumps(dict(email=email, tier=tier)),
                                             content_type='application/json', follow_redirects=True)
        assert register_response.status_code == status_code


@pytest.mark.parametrize("email,status_code", [
    ("admin@acme.org", 201),
    ("tristan", 403),
    ("invalid@domain.org", 403)
])
def test_register_api(init_database, test_client, email, status_code):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/register/' api is posted to (POST)
    THEN check the response
    """
    register_response = test_client.post('/api/v1/auth/register/',
                                         data=json.dumps(dict(email=email, password='TestPassword')),
                                         content_type='application/json', follow_redirects=True)

    assert register_response.status_code == status_code


@pytest.mark.parametrize("tier,status_code", [
    ('admin', 403),
    ('superadmin', 200),
])
def test_blockchain_key_api(test_client, authed_sempo_admin_user, tier, status_code):
    """
    GIVEN a Flask application
    WHEN '/api/auth/blockchain/' is requested (GET)
    THEN check the response is only returned for is_superadmin
    """

    authed_sempo_admin_user.set_held_role('ADMIN',tier)
    response = test_client.get('/api/v1/auth/blockchain/',
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
    response = test_client.get('/api/v1/auth/permissions/',
                               headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 200
    assert response.json['data']['admins'] is not None
    assert isinstance(response.json['data']['admins'], list)


def get_admin_default_org_id(admin_user):
    return admin_user.default_organisation_id


@pytest.mark.parametrize("creator_tier, email, invitee_tier, organisation_id_selector, response_code", [
    ('admin', 'foo1@acme.com', 'admin', lambda o: 2, 401),
    ('admin', 'foo1@acme.com', 'admin', lambda o: None, 201),
    ('sempoadmin', 'foo@acme.com', 'admin', lambda o: 12332, 404),
    ('sempoadmin',  None, 'admin', get_admin_default_org_id, 400),
    ('sempoadmin', 'foo@acme.com', None, get_admin_default_org_id, 400),
    ('sempoadmin', 'foo@acme.com', 'admin', get_admin_default_org_id, 201),
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

    default_org_id = get_admin_default_org_id(authed_sempo_admin_user)

    response = test_client.post(f'/api/v1/auth/permissions/?org={default_org_id}',
                                headers=dict(
                                    Authorization=get_complete_auth_token(authed_sempo_admin_user),
                                    Accept='application/json'
                                ),
                                json={'email': email, 'tier': invitee_tier, 'organisation_id': organisation_id})

    assert response.status_code == response_code


def test_get_external_credentials_api(test_client, authed_sempo_admin_user):
    """
    GIVEN a Flask Application
    WHEN '/api/auth/external/' is requested (GET)
    THEN check external details username and password are returned
    """
    authed_sempo_admin_user.is_activated = True
    authed_sempo_admin_user.TFA_enabled = True
    authed_sempo_admin_user.set_held_role('ADMIN', 'admin')
    auth_token = authed_sempo_admin_user.encode_auth_token().decode()
    tfa_token = authed_sempo_admin_user.encode_TFA_token(9999).decode()
    response = test_client.get('/api/v1/auth/external/',
                               headers=dict(Authorization=auth_token + '|' + tfa_token, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == 200
    assert response.json['username'] == 'admin_sempo'
    org = Organisation.query.filter_by(external_auth_username = response.json['username']).first()
    assert response.json['password'] == org.external_auth_password

def test_logout_api(test_client, authed_sempo_admin_user):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/logout/' api is posted to (POST)
    THEN check response is 200 and auth_token is added to blacklist
    """
    from server.models.blacklist_token import BlacklistToken
    authed_sempo_admin_user.is_activated = True
    auth_token = authed_sempo_admin_user.encode_auth_token().decode()
    response = test_client.post('/api/v1/auth/logout/',
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

    response = test_client.post('/api/v1/auth/reset_password/',
                                data=json.dumps(dict(new_password=password, reset_password_token=password_reset_token)),
                                content_type='application/json', follow_redirects=True)

    f = Fernet(config.PASSWORD_PEPPER)
    decrypted_hash = f.decrypt(authed_sempo_admin_user.password_hash.encode())
    assert bcrypt.checkpw(
        password.encode(), decrypted_hash)
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
    test_client.post('/api/v1/auth/reset_password/',
                            data=json.dumps(
                            dict(new_password=password, reset_password_token=password_reset_token)),
                            content_type='application/json', follow_redirects=True)

    # Use password for the second time
    response = test_client.post('/api/v1/auth/reset_password/',
                                data=json.dumps(
                                dict(new_password=password, reset_password_token=password_reset_token)),
                                content_type='application/json', follow_redirects=True)

    assert response.status_code == 401
    assert response.json['message'] == 'Token already used'

@pytest.mark.parametrize("username,password,status_code", [
    (interal_auth_username, interal_auth_password, 200),
    (external_auth_username, external_auth_password, 200),
    (fake_username, fake_password, 401),
    (None, None, 401)
])
def test_basic_auth(test_client, authed_sempo_admin_user, username, password, status_code):
    """
    GIVEN a Flask Application
    WHEN the '/api/auth/check/basic/' api is requested (GET)
    THEN check the response is valid
    """

    if username and password:
        basic_auth = 'Basic ' + base64.b64encode(
            bytes(username() + ":" + password(), 'ascii')).decode('ascii')
    else:
        basic_auth = ''

    response = test_client.get('/api/v1/auth/check/basic/',
                               headers=dict(Authorization=basic_auth, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code

@pytest.mark.parametrize("username,password,status_code", [
    (interal_auth_username, interal_auth_password, 401),
    (external_auth_username, external_auth_password, 401),
    (fake_username, fake_password, 401),
    (None, None, 401)
])
def test_correctly_reject_basic_auth(test_client, authed_sempo_admin_user, username, password, status_code):
    """
    GIVEN a Flask Application
    WHEN the '/api/auth/check/basic/' api is requested (GET)
    THEN check the response is valid
    """

    if username and password:
        basic_auth = 'Basic ' + base64.b64encode(
            bytes(username() + ":" + password(), 'ascii')).decode('ascii')
    else:
        basic_auth = ''

    response = test_client.get('/api/v1/auth/check/token/',
                               headers=dict(Authorization=basic_auth, Accept='application/json'),
                               content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code

@pytest.mark.parametrize("username,password,status_code", [
    (interal_auth_username, interal_auth_password, 200),
    (external_auth_username, external_auth_password, 200),
    (fake_username, fake_password, 401),
    (None, None, 401)
])
def test_basic_query_string_auth(test_client, username, authed_sempo_admin_user, password, status_code):
    """
    GIVEN a Flask Application
    WHEN the '/api/auth/check/basic/' api is requested (GET) with credentials in query string
    THEN check the response is valid
    """

    if username and password:
        query = f'?username={username()}&password={password()}'
    else:
        query = ''

    response = test_client.get('/api/v1/auth/check/basic/' + query,
                               content_type='application/json', follow_redirects=True)

    assert response.status_code == status_code


@pytest.mark.parametrize("role, tier,status_code", [
    (None, None, 401),
    ('VENDOR', 'supervendor', 403),
    ('ADMIN', 'admin', 403),
    ('ADMIN', 'superadmin', 200),
])
def test_token_auth(test_client, authed_sempo_admin_user, role, tier, status_code):
    """
    GIVEN a Flask application
    WHEN the '/api/auth/check/token/' api is requested (GET)
    THEN check the response is only returned for superadmin
    """

    if role and tier:
        authed_sempo_admin_user.set_held_role('ADMIN', None)
        authed_sempo_admin_user.set_held_role(role, tier)
        auth = get_complete_auth_token(authed_sempo_admin_user)
    else:
        auth = None

    response = test_client.get('/api/v1/auth/check/token/',
                               headers=dict(
                                   Authorization=auth,
                                   Accept='application/json'
                               ),
                               content_type='application/json', follow_redirects=True)
    assert response.status_code == status_code
