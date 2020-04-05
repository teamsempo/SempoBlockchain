import pytest, datetime
from server.utils.access_control import AccessControl
from server.exceptions import ResourceAlreadyDeletedError, TransferAccountDeletionError

def test_new_sempo_admin_user(new_sempo_admin_user):
    """
    GIVEN a User model
    WHEN a new admin User is created
    THEN check the email, password is hashed, not authenticated, and role fields are defined correctly
    """
    assert new_sempo_admin_user.email == 'tristan@withsempo.com'
    assert new_sempo_admin_user.password_hash is not None
    assert new_sempo_admin_user.password_hash != 'TestPassword'
    assert not new_sempo_admin_user.is_activated
    assert AccessControl.has_any_tier(new_sempo_admin_user.roles, 'ADMIN')
    assert isinstance(new_sempo_admin_user.secret, str)

def test_authed_sempo_admin_user(authed_sempo_admin_user):


    """
    GIVEN a User model
    WHEN a new User is created in DB
    THEN check id, secret, has any admin role, created
    """
    assert isinstance(authed_sempo_admin_user.id, int)
    assert isinstance(authed_sempo_admin_user.secret, str)
    assert isinstance(authed_sempo_admin_user.created, object)


def test_update_admin_user_tier(new_sempo_admin_user):
    """
    GIVEN a User model
    WHEN a user tier is updated to superadmin
    THEN check that all lower tiers are True
    """
    new_sempo_admin_user.set_held_role('ADMIN', 'view')

    assert AccessControl.has_any_tier(new_sempo_admin_user.roles, 'ADMIN')
    assert not AccessControl.has_sufficient_tier(new_sempo_admin_user.roles, 'ADMIN', 'subadmin')
    assert not AccessControl.has_sufficient_tier(new_sempo_admin_user.roles, 'ADMIN', 'admin')
    assert not AccessControl.has_sufficient_tier(new_sempo_admin_user.roles, 'ADMIN', 'superadmin')

    # update user tier to super admin
    new_sempo_admin_user.set_held_role('ADMIN', 'superadmin')

    assert AccessControl.has_any_tier(new_sempo_admin_user.roles, 'ADMIN')
    assert AccessControl.has_sufficient_tier(new_sempo_admin_user.roles, 'ADMIN', 'subadmin')
    assert AccessControl.has_sufficient_tier(new_sempo_admin_user.roles, 'ADMIN', 'admin')
    assert AccessControl.has_sufficient_tier(new_sempo_admin_user.roles, 'ADMIN', 'superadmin')


def test_update_password(new_sempo_admin_user):
    """
    GIVEN a User model
    WHEN a new password set
    THEN check password is hashed and verify password hash
    """
    new_password = 'NewTestPassword'
    new_sempo_admin_user.hash_password(new_password)  # set new password
    assert new_sempo_admin_user.password_hash != new_password
    assert new_sempo_admin_user.verify_password(new_password)


def test_valid_activation_token(new_sempo_admin_user):
    """
    GIVEN a User model
    WHEN a activation token is created
    THEN check token is valid
    """
    activation_token = new_sempo_admin_user.encode_single_use_JWS('A')
    assert activation_token is not None
    validity_check = new_sempo_admin_user.decode_single_use_JWS(activation_token, 'A')
    assert validity_check['success']


def test_valid_auth_token(authed_sempo_admin_user):
    """
    GIVEN A User Model
    WHEN a auth token is created
    THEN check it is a valid auth token
    """
    auth_token = authed_sempo_admin_user.encode_auth_token()
    assert auth_token is not None
    resp = authed_sempo_admin_user.decode_auth_token(auth_token.decode())
    assert not isinstance(auth_token, str)
    assert (authed_sempo_admin_user.query.execution_options(show_all=True)
            .filter_by(id=resp['id']).first()
            is not None)


def test_tfa_required(authed_sempo_admin_user):
    """
    GIVEN a User Model
    WHEN is_TFA_required is called
    THEN check returns config values
    """
    import config
    tiers = config.TFA_REQUIRED_ROLES
    authed_sempo_admin_user.set_held_role('ADMIN', 'view')
    assert authed_sempo_admin_user.is_TFA_required() is False
    for tier in tiers:
        authed_sempo_admin_user.set_held_role('ADMIN', tier)
        assert authed_sempo_admin_user.is_TFA_required() is True


def test_tfa_url(authed_sempo_admin_user):
    """
    GIVEN a User Model
    WHEN a tfa_url is created
    THEN check it has the correct email and secret
    """
    from urllib.parse import quote
    assert quote(authed_sempo_admin_user.email) in authed_sempo_admin_user.tfa_url
    assert quote(authed_sempo_admin_user.get_TFA_secret()) in authed_sempo_admin_user.tfa_url


def test_valid_tfa_token(authed_sempo_admin_user):
    """
    GIVEN A User Model
    WHEN a tfa token is created
    THEN check it is a valid tfa token
    """
    tfa_token = authed_sempo_admin_user.encode_TFA_token()
    assert tfa_token is not None
    resp = authed_sempo_admin_user.decode_auth_token(tfa_token.decode())
    assert not isinstance(tfa_token, str)
    assert (authed_sempo_admin_user.query.execution_options(show_all=True)
            .filter_by(id=resp['id']).first()
            is not None)


def test_delete_user_and_transfer_account(create_transfer_account_user):
    """
    GIVEN a User Model
    WHEN delete_user_and_transfer_account is called
    THEN check that raises an error when balance > 0, check PII is deleted, check duplication deletion fails
    """
    create_transfer_account_user.transfer_account.balance = 10

    with pytest.raises(TransferAccountDeletionError):
        create_transfer_account_user.delete_user_and_transfer_account()

    create_transfer_account_user.transfer_account.balance = 0

    create_transfer_account_user.delete_user_and_transfer_account()
    assert create_transfer_account_user.first_name is None
    assert create_transfer_account_user.last_name is None
    assert create_transfer_account_user.phone is None

    assert create_transfer_account_user.deleted is not None
    assert isinstance(create_transfer_account_user.deleted, datetime.datetime)

    assert create_transfer_account_user.transfer_account.deleted is not None
    assert isinstance(create_transfer_account_user.transfer_account.deleted, datetime.datetime)

    with pytest.raises(ResourceAlreadyDeletedError):
        create_transfer_account_user.delete_user_and_transfer_account()
