import pytest
import datetime
import jwt
from server.utils.auth import tfa_logic, get_complete_auth_token
from flask import current_app


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
