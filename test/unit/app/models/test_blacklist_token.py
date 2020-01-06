
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

    assert create_blacklisted_token.check_blacklist(create_blacklisted_token.token)
    assert not create_blacklisted_token.check_blacklist(authed_sempo_admin_user.encode_auth_token())
