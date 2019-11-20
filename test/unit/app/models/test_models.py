"""
This file (test_models.py) contains the unit tests for the models.py file.
"""
import pytest
from server.exceptions import IconNotSupportedException, PaymentMethodException, AccountLimitError
from server.utils.access_control import AccessControl

""" ----- Organisation Model ----- """
#
#
# def test_create_organisation(create_organisation):
#     """
#     GIVEN an Organisation model
#     WHEN a new Organisation is created in DB
#     THEN check id, name exist AND users, transfer_accounts and credit_transfers is None
#     """
#     assert isinstance(create_organisation.id, int)
#     assert create_organisation.name == 'Sempo'
#
#     assert create_organisation.users is None
#     assert create_organisation.transfer_accounts is None
#     assert create_organisation.credit_transfers is None
#
#
# def test_create_organisation_with_associations(create_organisation, new_sempo_admin_user):
#     """
#     GIVEN an Organisation and User Model
#     WHEN a user is
#     """
#

""" ----- User Model ----- """


def test_new_sempo_admin_user(new_sempo_admin_user):
    """
    GIVEN a User model
    WHEN a new admin User is created
    THEN check the email, password is hashed, not authenticated, and role fields are defined correctly
    """
    assert new_sempo_admin_user.email == 'tristan@sempo.ai'
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
    resp = authed_sempo_admin_user.decode_auth_token(auth_token.decode())  # todo- patch .decode()
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


def test_get_most_relevant_transfer_usage(authed_sempo_admin_user):
    """
    GIVEN A User Model
    WHEN get_most_relevant_transfer_usage is called
    THEN a list is returnen
    """
    # TODO This test in pretty lightweight atm it just checks if a list
    # is returned. It may be worthwhile to add more extensive testing in
    # the future.
    usages = authed_sempo_admin_user.get_most_relevant_transfer_usage()
    assert isinstance(usages, list)


""" ----- Transfer Account Model ----- """


def test_create_transfer_account(create_transfer_account):
    """
    GIVEN A transfer account model
    WHEN a new transfer account is created
    THEN check a blockchain address is created, default balance is 0
    """
    assert create_transfer_account.balance == 0
    assert create_transfer_account.blockchain_address is not None


# todo- requires mocking blockchain worker/endpoint.
# def test_approve_beneficiary_transfer_account(new_transfer_account):
#     """
#     GIVEN a Transfer Account model
#     WHEN a new transfer account is created AND approved
#     THEN check a BENEFICIARY is disbursed initial balance
#     """
#     import config
#     new_transfer_account.is_beneficiary = True
#     new_transfer_account.approve()
#
#     assert new_transfer_account.balance is config.STARTING_BALANCE


def test_approve_vendor_transfer_account(new_transfer_account):
    """
    GIVEN a Transfer Account model
    WHEN a new transfer account is created and approved
    THEN check a VENDOR is NOT disbursed initial balance
    """
    new_transfer_account.is_vendor = True
    new_transfer_account.approve()

    assert new_transfer_account.balance == 0


""" ----- Credit Transfer Model ----- """


def test_new_credit_transfer_complete(create_credit_transfer):
    """
    GIVEN a CreditTransfer model
    WHEN a new credit transfer is created
    THEN check transfer status is PENDING, then resolve as complete
    """
    from server.utils.transfer_enums import TransferStatusEnum
    from flask import g
    g.celery_tasks = []
    assert isinstance(create_credit_transfer.transfer_amount, float)
    assert create_credit_transfer.transfer_amount == 1000
    assert create_credit_transfer.transfer_status is TransferStatusEnum.PENDING
    create_credit_transfer.resolve_as_completed()  # complete credit transfer
    assert create_credit_transfer.transfer_status is TransferStatusEnum.COMPLETE


def test_new_credit_transfer_rejected(create_credit_transfer):
    """
    GIVEN a CreditTransfer model
    WHEN a new credit transfer is created
    THEN check transfer status is PENDING, then resolve as rejected with message,
         check status is REJECTED and message is not NONE
    """
    from server.utils.transfer_enums import TransferStatusEnum
    assert create_credit_transfer.transfer_status is TransferStatusEnum.PENDING

    create_credit_transfer.resolve_as_rejected(
        message="Sender {} has insufficient balance".format(create_credit_transfer.sender_transfer_account)
    )  # reject credit transfer

    assert create_credit_transfer.transfer_status is TransferStatusEnum.REJECTED
    assert create_credit_transfer.resolution_message is not None


def test_new_credit_transfer_check_sender_transfer_limits(create_credit_transfer):
    """
    GIVEN a CreditTransfer model
    WHEN a new credit transfer is created
    THEN check the correct check_sender_transfer_limits apply
    """
    from server.utils.transaction_limits import LIMITS
    from server.models.kyc_application import KycApplication
    from server.models import token
    from server.utils.transfer_enums import TransferTypeEnum

    # Sempo Level 0 LIMITS (payment only)
    assert create_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMITS
        if limit.name == 'Sempo Level 0'
        and str(create_credit_transfer.transfer_type) in limit.applied_to_transfer_types
    ]

    # Check Sempo Level 1 LIMITS (payment only)
    create_credit_transfer.sender_user.is_phone_verified = True
    assert create_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMITS
        if limit.name == 'Sempo Level 1'
        and str(create_credit_transfer.transfer_type) in limit.applied_to_transfer_types
    ]

    # Check Sempo Level 2 LIMITS (payment only)
    kyc = KycApplication(type='INDIVIDUAL')
    kyc.user = create_credit_transfer.sender_user
    kyc.kyc_status = 'VERIFIED'
    assert create_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMITS
        if limit.name == 'Sempo Level 2'
        and str(create_credit_transfer.transfer_type) in limit.applied_to_transfer_types
    ]

    # Check Sempo Level 3 LIMITS (payment only)
    kyc.type = 'BUSINESS'
    assert create_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMITS
        if limit.name == 'Sempo Level 3'
        and str(create_credit_transfer.transfer_type) in limit.applied_to_transfer_types
    ]

    # Check GE LIMITS for Liquid Token (withdrawal only)
    create_credit_transfer.token.token_type = token.TokenType.LIQUID
    create_credit_transfer.transfer_type = "WITHDRAWAL"
    create_credit_transfer.sender_transfer_account.balance = 10000
    assert create_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMITS
        if limit.name == 'GE Liquid Token - Standard User'
        and str(create_credit_transfer.transfer_type) in limit.applied_to_transfer_types
    ]

    # Check Limits skipped if no sender user (exchange)
    create_credit_transfer.sender_user = None
    create_credit_transfer.transfer_type = TransferTypeEnum.EXCHANGE
    assert create_credit_transfer.check_sender_transfer_limits() is None


def test_new_credit_transfer_check_sender_transfer_limits_exception(external_reserve_token, create_credit_transfer):
    """
    GIVEN a CreditTransfer model
    WHEN a new credit transfer is created
    THEN check the correct check_sender_transfer_limits raises AccountLimitError
    """
    from server.utils.transaction_limits import LIMITS
    from server.models import credit_transfer, token
    from server import db

    create_credit_transfer.token.token_type = token.TokenType.RESERVE
    create_credit_transfer.sender_user.kyc_applications = []

    # Sempo Level 0 LIMITS (payment only) on init
    with pytest.raises(AccountLimitError):
        c = credit_transfer.CreditTransfer(
            amount=1000000,
            token=external_reserve_token,
            sender_user=create_credit_transfer.sender_user,
            recipient_user=create_credit_transfer.sender_user,
            transfer_type='PAYMENT'
        )
        db.session.add(c)
        db.session.flush()

    # Sempo Level 0 LIMITS (payment only) on check LIMITS
    with pytest.raises(AccountLimitError):
        create_credit_transfer.check_sender_transfer_limits()

    # Check GE LIMITS for Liquid Token (withdrawal only) on check LIMITS
    create_credit_transfer.token.token_type = token.TokenType.LIQUID
    create_credit_transfer.transfer_type = "WITHDRAWAL"
    create_credit_transfer.sender_transfer_account.balance = 1000
    with pytest.raises(AccountLimitError):
        assert create_credit_transfer.check_sender_transfer_limits() == [
            limit for limit in LIMITS
            if limit.name == 'GE Liquid Token - Standard User'
            and str(create_credit_transfer.transfer_type) in limit.applied_to_transfer_types
        ]


""" ----- Blacklisted Token Model ----- """


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


""" ----- Transfer Usage Model ----- """


def test_create_transfer_usage(create_transfer_usage):
    """
    GIVEN a TransferUsage Model
    WHEN a new Transfer Usage is created
    THEN check id, created, name, icon, translations
    """
    assert isinstance(create_transfer_usage.id, int)
    assert isinstance(create_transfer_usage.created, object)

    assert create_transfer_usage.name == 'Food'
    assert create_transfer_usage.icon == 'food-apple'
    assert create_transfer_usage.translations == dict(en='Food', fr='aliments')


def test_create_transfer_usage_exception(create_transfer_usage):
    """
    GIVEN a TransferUsage Model
    WHEN a new Transfer Usage is created and the icon is not supported
    THEN check the IconNotSupportedException is raised
    """
    with pytest.raises(IconNotSupportedException):
        create_transfer_usage.icon = 'bananaaaas'


""" ----- IP Address Model ----- """


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


""" ----- FiatRamp Model ----- """


def test_new_fiat_ramp(create_fiat_ramp):
    """
    GIVEN a FiatRamp model
    WHEN a new fiat ramp transfer is created
    THEN check transfer status is PENDING, then resolve as complete
    """
    from server.models.fiat_ramp import FiatRampStatusEnum

    assert isinstance(create_fiat_ramp.payment_amount, int)
    assert create_fiat_ramp.payment_amount == 100
    assert create_fiat_ramp.payment_reference is not None

    assert create_fiat_ramp.payment_status is FiatRampStatusEnum.PENDING

    create_fiat_ramp.resolve_as_completed()

    assert create_fiat_ramp.payment_status is FiatRampStatusEnum.COMPLETE


def test_new_fiat_ramp_type_exception(create_fiat_ramp):
    """
    GIVEN a FiatRamp Model
    WHEN a new FiatRamp is created and the payment_method is not supported
    THEN check the PaymentMethodException is raised
    """
    with pytest.raises(PaymentMethodException):
        create_fiat_ramp.payment_method = 'UNSUPPORTED_PAYMENT_METHOD'
