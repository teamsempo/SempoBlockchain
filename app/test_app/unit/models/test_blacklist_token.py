from server.models.user import User

def test_create_blacklisted_token(create_blacklisted_token, authed_sempo_admin_user):
    """
    GIVEN a BlacklistToken Model
    WHEN a new blacklisted token is created
    THEN check blacklisted_on and check_blacklist
    """
    import datetime
    assert isinstance(create_blacklisted_token.id, int)
    assert isinstance(create_blacklisted_token.created, object)
    assert datetime.datetime.now() - create_blacklisted_token.blacklisted_on <= datetime.timedelta(seconds=5)
    assert User.decode_auth_token(create_blacklisted_token.token) == "Token blacklisted. Please log in again."
    # Login Again
    import time
    time.sleep(1)
    token = authed_sempo_admin_user.encode_auth_token()
    assert User.decode_auth_token(token)['id']