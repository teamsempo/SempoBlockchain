import pytest

from server.exceptions import (
    TransferLimitError,
    TransferCountLimitError,
    TransferBalanceFractionLimitError,
    MinimumSentLimitError,
    MaximumPerTransferLimitError
)

from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum
from server.sempo_types import TransferAmount


def test_new_credit_transfer_check_sender_transfer_limits(new_credit_transfer):
    """
    GIVEN a CreditTransfer model
    WHEN a new credit transfer is created
    THEN check the correct check_sender_transfer_limits apply
    """
    from server.utils.transfer_limits import LIMIT_IMPLEMENTATIONS
    from server.models.kyc_application import KycApplication
    from server.models import token

    # Sempo Level 0 LIMITS (payment only)
    assert new_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMIT_IMPLEMENTATIONS
        if 'Sempo Level 0: P' in limit.name
    ]

    # Check Sempo Level 1 LIMITS (payment only)
    new_credit_transfer.sender_user.is_phone_verified = True
    assert new_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMIT_IMPLEMENTATIONS
        if 'Sempo Level 1: P' in limit.name
    ]

    # Check Sempo Level 2 LIMITS (payment only)
    kyc = KycApplication(type='INDIVIDUAL')
    kyc.user = new_credit_transfer.sender_user
    kyc.kyc_status = 'VERIFIED'
    assert new_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMIT_IMPLEMENTATIONS
        if 'Sempo Level 2: P' in limit.name
    ]

    # Check Sempo Level 3 LIMITS for business (payment only)
    kyc.type = 'BUSINESS'
    assert new_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMIT_IMPLEMENTATIONS
        if 'Sempo Level 3: P' in limit.name
    ]

    # Check Sempo Level 3 LIMITS for multiple verified (payment only)
    kyc.type = 'INDIVIDUAL'
    kyc.multiple_documents_verified = True
    assert new_credit_transfer.check_sender_transfer_limits() == [
        limit for limit in LIMIT_IMPLEMENTATIONS
        if 'Sempo Level 3: P' in limit.name
    ]

    # Check additional GE LIMITS for Liquid Token (withdrawal)
    new_credit_transfer.token.token_type = token.TokenType.LIQUID
    new_credit_transfer.transfer_type = TransferTypeEnum.WITHDRAWAL
    new_credit_transfer.sender_transfer_account.set_balance_offset(10000)
    assert new_credit_transfer.get_transfer_limits() == [
        limit for limit in LIMIT_IMPLEMENTATIONS
        if 'GE Liquid Token - Standard User' == limit.name or 'Sempo Level 3: WD' in limit.name
    ]

    # Check additional GE LIMITS for Liquid Token (payment, Agent Out Subtype)
    new_credit_transfer.token.token_type = token.TokenType.LIQUID
    new_credit_transfer.transfer_type = TransferTypeEnum.PAYMENT
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    new_credit_transfer.sender_transfer_account.set_balance_offset(10000)
    assert new_credit_transfer.get_transfer_limits() == [
        limit for limit in LIMIT_IMPLEMENTATIONS
        if 'GE Liquid Token - Standard User' in limit.name or 'Sempo Level 3: P' in limit.name
    ]

    # Check additional GE LIMITS for Liquid Token and Group Account (payment, Agent Out Subtype)
    new_credit_transfer.sender_user.set_held_role('GROUP_ACCOUNT', 'group_account')
    new_credit_transfer.token.token_type = token.TokenType.LIQUID
    new_credit_transfer.transfer_type = TransferTypeEnum.PAYMENT
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    new_credit_transfer.sender_transfer_account.set_balance_offset(10000)
    assert new_credit_transfer.get_transfer_limits() == [
        limit for limit in LIMIT_IMPLEMENTATIONS
        if 'GE Liquid Token - Group Account User' in limit.name or 'Sempo Level 3: P' in limit.name
    ]

def test_new_credit_transfer_check_sender_transfer_limits_for_exchange(new_credit_transfer):
    # Check Limits skipped if no sender user (exchange)
    new_credit_transfer.sender_user = None
    new_credit_transfer.transfer_type = TransferTypeEnum.EXCHANGE
    assert new_credit_transfer.check_sender_transfer_limits() is None


def test_new_credit_transfer_check_sender_transfer_limits_exception_on_init(external_reserve_token, new_credit_transfer):
    from server.models import credit_transfer, token
    from server import db

    new_credit_transfer.token.token_type = token.TokenType.RESERVE
    new_credit_transfer.sender_user.kyc_applications = []

    # Sempo Level 0 LIMITS (payment only) on init
    with pytest.raises(TransferLimitError):
        c = credit_transfer.CreditTransfer(
            amount=1000000,
            token=external_reserve_token,
            sender_user=new_credit_transfer.sender_user,
            recipient_user=new_credit_transfer.sender_user,
            transfer_type=TransferTypeEnum.PAYMENT,
            transfer_subtype=TransferSubTypeEnum.STANDARD,
            require_sufficient_balance=False
        )
        db.session.add(c)
        c.resolve_as_complete_and_trigger_blockchain()
        db.session.flush()

def test_liquidtoken_number_of_limits(new_credit_transfer):
    from server.models import token

    new_credit_transfer.sender_user.set_held_role('GROUP_ACCOUNT', 'group_account')

    new_credit_transfer.transfer_type = TransferTypeEnum.PAYMENT
    new_credit_transfer.token.token_type = token.TokenType.LIQUID
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    assert len(new_credit_transfer.get_transfer_limits()) == 6


def test_liquidtoken_fraction_limit(new_credit_transfer):
    from server.models import token

    # Check GE LIMITS for Liquid Token (payment, agent_out subtype) on check LIMITS
    new_credit_transfer.transfer_type = TransferTypeEnum.PAYMENT
    new_credit_transfer.token.token_type = token.TokenType.LIQUID
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT

    new_credit_transfer.sender_transfer_account.set_balance_offset(1000)
    new_credit_transfer.sender_user.set_held_role('GROUP_ACCOUNT', 'group_account')

    with pytest.raises(TransferBalanceFractionLimitError):
        new_credit_transfer.check_sender_transfer_limits()


def test_liquidtoken_min_send_limit(new_credit_transfer):
    from server.models import token
    # Check GE LIMITS for Liquid Token (payment, agent_out subtype) on check LIMITS
    new_credit_transfer.transfer_type = TransferTypeEnum.PAYMENT
    new_credit_transfer.token.token_type = token.TokenType.LIQUID
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    new_credit_transfer.transfer_amount = 1500
    new_credit_transfer.sender_transfer_account.set_balance_offset(10000)
    new_credit_transfer.sender_user.set_held_role('GROUP_ACCOUNT', 'group_account')

    with pytest.raises(MinimumSentLimitError):
        new_credit_transfer.check_sender_transfer_limits()


def test_liquidtoken_count_limit(new_credit_transfer, other_new_credit_transfer):
    from server.models import token
    # Check GE LIMITS for Liquid Token (payment, agent_out subtype) on check LIMITS
    new_credit_transfer.transfer_type = TransferTypeEnum.PAYMENT
    new_credit_transfer.token.token_type = token.TokenType.LIQUID
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT

    other_new_credit_transfer.transfer_type = TransferTypeEnum.PAYMENT
    other_new_credit_transfer.token.token_type = token.TokenType.LIQUID
    other_new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    other_new_credit_transfer.sender_transfer_account.set_balance_offset(10000)
    other_new_credit_transfer.sender_user.set_held_role('GROUP_ACCOUNT', 'group_account')

    with pytest.raises(TransferCountLimitError):
        other_new_credit_transfer.check_sender_transfer_limits()


def test_liquidtoken_max_amount_limit(new_credit_transfer, mocker):
    from server.models import token


    from server.utils.transfer_limits import (
        AGENT_OUT_PAYMENT,
        WITHDRAWAL,
        is_group_and_liquid_token,
        MaximumAmountPerTransferLimit)

    from server.utils import transfer_limits

    # The max per-amount transfer limit is higher than the KYC classes, so it's easier to test by patching
    patched_limit = [
        MaximumAmountPerTransferLimit('GE Liquid Token - Group Account User',
                                     [AGENT_OUT_PAYMENT, WITHDRAWAL],
                                     is_group_and_liquid_token,
                                     maximum_amount=10)

    ]

    mocker.patch.object(transfer_limits, 'LIMIT_IMPLEMENTATIONS', patched_limit)

    new_credit_transfer.transfer_type = TransferTypeEnum.PAYMENT
    new_credit_transfer.token.token_type = token.TokenType.LIQUID
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT

    new_credit_transfer.sender_transfer_account.set_balance_offset(10000)
    new_credit_transfer.sender_user.set_held_role('GROUP_ACCOUNT', 'group_account')

    with pytest.raises(MaximumPerTransferLimitError):
        new_credit_transfer.check_sender_transfer_limits()


def test_new_credit_transfer_check_sender_transfer_limits_exception_on_check_limits(new_credit_transfer):
    from server.models import token

    new_credit_transfer.transfer_amount = 100000

    new_credit_transfer.token.token_type = token.TokenType.RESERVE
    new_credit_transfer.sender_user.kyc_applications = []

    # Sempo Level 0 LIMITS (payment only) on check LIMITS
    with pytest.raises(TransferLimitError):
        new_credit_transfer.check_sender_transfer_limits()


def test_sempoadmin_doesnt_have_limits(new_credit_transfer):
    from server.models import token

    new_credit_transfer.transfer_amount = 100000

    new_credit_transfer.token.token_type = token.TokenType.RESERVE
    new_credit_transfer.sender_user.kyc_applications = []
    new_credit_transfer.sender_user.set_held_role('ADMIN', 'sempoadmin')

    new_credit_transfer.check_sender_transfer_limits()

    new_credit_transfer.sender_user.set_held_role('ADMIN', None)


def test_new_credit_transfer_check_sender_transfer_limits_exception_ge_withdrawal(new_credit_transfer):
    from server.models import token
    # Check GE LIMITS for Liquid Token (withdrawal) on check LIMITS
    new_credit_transfer.token.token_type = token.TokenType.LIQUID
    new_credit_transfer.transfer_type = TransferTypeEnum.WITHDRAWAL
    new_credit_transfer.sender_transfer_account.set_balance_offset(1000)
    with pytest.raises(TransferLimitError):
        new_credit_transfer.check_sender_transfer_limits()


def test_new_credit_transfer_check_sender_transfer_limits_exception_ge_agent_out(new_credit_transfer):
    from server.models import token
    # Check GE LIMITS for Liquid Token (payment, agent_out subtype) on check LIMITS
    new_credit_transfer.transfer_type = TransferTypeEnum.PAYMENT
    new_credit_transfer.token.token_type = token.TokenType.LIQUID
    new_credit_transfer.transfer_subtype = TransferSubTypeEnum.AGENT_OUT
    new_credit_transfer.sender_transfer_account.set_balance_offset(1000)
    with pytest.raises(TransferLimitError):
        new_credit_transfer.check_sender_transfer_limits()

