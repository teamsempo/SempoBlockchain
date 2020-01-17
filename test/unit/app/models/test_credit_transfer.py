import pytest
from server.exceptions import AccountLimitError
from server.utils.transfer_enums import TransferSubTypeEnum, TransferTypeEnum


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


# TODO: split this out for proper unit test. Also there should be tests that actually run against the counts.
def test_new_credit_transfer_check_sender_transfer_limits(create_credit_transfer):
    """
    GIVEN a CreditTransfer model
    WHEN a new credit transfer is created
    THEN check the correct check_sender_transfer_limits apply
    """
    from server.utils.transfer_limits import LIMITS
    from server.models.kyc_application import KycApplication
    from server.models import token

    # Sempo Level 0 LIMITS (payment only)
    assert create_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMITS
        if 'Sempo Level 0: P' in limit.name
    ]

    # Check Sempo Level 1 LIMITS (payment only)
    create_credit_transfer.sender_user.is_phone_verified = True
    assert create_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMITS
        if 'Sempo Level 1: P' in limit.name
    ]

    # Check Sempo Level 2 LIMITS (payment only)
    kyc = KycApplication(type='INDIVIDUAL')
    kyc.user = create_credit_transfer.sender_user
    kyc.kyc_status = 'VERIFIED'
    assert create_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMITS
        if 'Sempo Level 2: P' in limit.name
    ]

    # Check Sempo Level 3 LIMITS (payment only)
    kyc.type = 'BUSINESS'
    assert create_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMITS
        if 'Sempo Level 3: P' in limit.name
    ]

    # Check additional GE LIMITS for Liquid Token (withdrawal)
    create_credit_transfer.token.token_type = token.TokenType.LIQUID
    create_credit_transfer.transfer_type = TransferTypeEnum.WITHDRAWAL
    create_credit_transfer.sender_transfer_account.balance = 10000
    assert create_credit_transfer.get_transfer_limits() == [
        limit for limit in LIMITS
        if 'GE Liquid Token - Standard User' == limit.name or 'Sempo Level 3: WD' in limit.name
    ]

    # Check additional GE LIMITS for Liquid Token (payment, Agent Out Subtype)
    create_credit_transfer.token.token_type = token.TokenType.LIQUID
    create_credit_transfer.transfer_type = TransferTypeEnum.PAYMENT
    create_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    create_credit_transfer.sender_transfer_account.balance = 10000
    assert create_credit_transfer.get_transfer_limits() == [
        limit for limit in LIMITS
        if 'GE Liquid Token - Standard User' in limit.name or 'Sempo Level 3: P' in limit.name
    ]

    # Check additional GE LIMITS for Liquid Token and Group Account (payment, Agent Out Subtype)
    create_credit_transfer.sender_user.set_held_role('GROUP_ACCOUNT', 'grassroots_group_account')
    create_credit_transfer.token.token_type = token.TokenType.LIQUID
    create_credit_transfer.transfer_type = TransferTypeEnum.PAYMENT
    create_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    create_credit_transfer.sender_transfer_account.balance = 10000
    assert create_credit_transfer.get_transfer_limits() == [
        limit for limit in LIMITS
        if 'GE Liquid Token - Group Account User' in limit.name or 'Sempo Level 3: P' in limit.name
    ]


def test_new_credit_transfer_check_sender_transfer_limits_for_exchange(create_credit_transfer):
    # Check Limits skipped if no sender user (exchange)
    create_credit_transfer.sender_user = None
    create_credit_transfer.transfer_type = TransferTypeEnum.EXCHANGE
    assert create_credit_transfer.check_sender_transfer_limits() is None


def test_new_credit_transfer_check_sender_transfer_limits_exception_on_init(external_reserve_token, create_credit_transfer):
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
            transfer_type=TransferTypeEnum.PAYMENT,
            transfer_subtype=TransferSubTypeEnum.STANDARD
        )
        db.session.add(c)
        c.resolve_as_completed()
        db.session.flush()


def test_new_credit_transfer_check_sender_transfer_limits_exception_on_check_limits(create_credit_transfer):
    from server.models import token

    create_credit_transfer.transfer_amount = 100000

    create_credit_transfer.token.token_type = token.TokenType.RESERVE
    create_credit_transfer.sender_user.kyc_applications = []

    # Sempo Level 0 LIMITS (payment only) on check LIMITS
    with pytest.raises(AccountLimitError):
        create_credit_transfer.check_sender_transfer_limits()


def test_new_credit_transfer_check_sender_transfer_limits_exception_ge_withdrawal(create_credit_transfer):
    from server.models import token
    # Check GE LIMITS for Liquid Token (withdrawal) on check LIMITS
    create_credit_transfer.token.token_type = token.TokenType.LIQUID
    create_credit_transfer.transfer_type = TransferTypeEnum.WITHDRAWAL
    create_credit_transfer.sender_transfer_account.balance = 1000
    with pytest.raises(AccountLimitError):
        create_credit_transfer.check_sender_transfer_limits()


def test_new_credit_transfer_check_sender_transfer_limits_exception_ge_agent_out(create_credit_transfer):
    from server.models import token
    # Check GE LIMITS for Liquid Token (payment, agent_out subtype) on check LIMITS
    create_credit_transfer.transfer_type = TransferTypeEnum.PAYMENT
    create_credit_transfer.token.token_type = token.TokenType.LIQUID
    create_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    create_credit_transfer.sender_transfer_account.balance = 1000
    with pytest.raises(AccountLimitError):
        create_credit_transfer.check_sender_transfer_limits()

