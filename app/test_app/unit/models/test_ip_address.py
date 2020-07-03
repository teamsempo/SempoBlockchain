

def test_create_ip_address(create_ip_address, authed_sempo_admin_user):
    """
    GIVEN a IpAddress Model
    WHEN a new Ip Address is created
    THEN check id, created, ip and check_user_ips
    """

    assert isinstance(create_ip_address.id, int)
    assert isinstance(create_ip_address.created, object)

    assert create_ip_address.ip == '210.18.192.196'
    assert create_ip_address.user_id == authed_sempo_admin_user.id

    assert create_ip_address.check_user_ips(authed_sempo_admin_user, '210.18.192.196')
    assert not create_ip_address.check_user_ips(authed_sempo_admin_user, '123.12.123.123')

