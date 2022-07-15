import pytest
import datetime
import jwt
from server.utils.auth import tfa_logic, get_complete_auth_token
from flask import current_app
from server import red

@pytest.mark.parametrize("no_token, tfa_enabled, invalid_token, invalid_user_id, message", [
    (True, True, None, None, 'TFA token required, none supplied'),
    (None, False, None, None, 'User must setup two factor authentication'),
    (None, True, True, None, 'Invalid TFA Token.'),
    (None, True, None, True, 'Invalid User ID in TFA response.'),
])
def test_tfa_logic_error(test_client, init_database, authed_sempo_admin_user, no_token, tfa_enabled, invalid_token,
                         invalid_user_id, message):
    user = authed_sempo_admin_user
    user.set_held_role('ADMIN', 'superadmin')
    user.TFA_enabled = tfa_enabled
    auth = get_complete_auth_token(authed_sempo_admin_user)
    tfa_token = None if no_token else auth.split('|')[1]

    if invalid_token:
        tfa_token = tfa_token + 'foo'

    if invalid_user_id:
        # build a fake tfa token with incorrect user ID
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1, seconds=30),
            'iat': datetime.datetime.utcnow(),
            'id': 123
        }

        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    tfa = tfa_logic(user=user, tfa_token=tfa_token)

    assert tfa['message'] == message

def test_rate_limited_login(test_client, init_database):
    # We need to disable IS_TEST to make rate limiting kick in!
    current_app.config['IS_TEST'] = False
    def flush_ratelimit_counter():
        red.delete('login_francine@cat.org')

    def attempt_login():
        return test_client.post(
            '/api/v1/auth/request_api_token/',
            headers=dict(
                Accept='application/json'
            ),
            json={
                'password': 'francineIsCat',
                'username': 'francine@cat.org'
            }).json

    # Flush rate limit counter in case of previous failed task            
    flush_ratelimit_counter()
    results = []
    for _ in range(27):
        results.append(attempt_login())
    for result in enumerate(results):
        if result[0] != 26:
            assert result[1] == {'message': 'Invalid username or password', 'status': 'fail'}
        else:
            assert result[1] == {'message': 'Please try again in 59 minutes', 'status': 'fail'}
    current_app.config['IS_TEST'] = True
    flush_ratelimit_counter()
