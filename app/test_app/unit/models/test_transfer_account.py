import pytest
from flask import g
from helpers.model_factories import CreditTransfer
from decimal import Decimal

def test_create_transfer_account(create_transfer_account):
    """
    GIVEN A transfer account model
    WHEN a new transfer account is created
    THEN check a blockchain address is created, default balance is 0
    """
    assert create_transfer_account.balance == 0
    assert create_transfer_account.blockchain_address is not None


def test_approve_vendor_transfer_account(create_transfer_account_user):
    """
    GIVEN a Transfer Account model
    WHEN a new transfer account is created and approved
    THEN check a VENDOR is NOT disbursed initial balance
    """
    create_transfer_account_user.transfer_account.is_beneficiary = False

    create_transfer_account_user.transfer_account.is_vendor = True
    create_transfer_account_user.transfer_account.approve_and_disburse()

    assert create_transfer_account_user.transfer_account.balance == 0


def test_balance_update_with_null_offset(create_transfer_account):
    """
    GIVEN a Transfer Account with a null offset(for example due to DB editing or migration)
    WHEN the balance is updated
    THEN check that the balance doesn't error out
    """

    create_transfer_account._balance_offset_wei = None
    create_transfer_account.update_balance()

def test_set_balance_offset(create_transfer_account):
    """
    GIVEN a Transfer Account
    WHEN the balance offset is updated
    THEN check that the function takes cents and stores in wei
    """

    create_transfer_account.set_balance_offset(123)
    assert create_transfer_account._balance_offset_wei == int(123e16)

def test_get_balance(create_transfer_account):
    """
    GIVEN a Transfer Account with a non-zero balance
    WHEN the balance is requested
    THEN check that the function goes from stored wei and returns cents
    """

    create_transfer_account._balance_wei = int(123e16)
    assert create_transfer_account.balance == 123

def test_balance_handles_pending_complete_statuses(new_credit_transfer):
    """
    Make sure that pending transfers are deducted from the sender's balance, but NOT added to the recipient's,
    while complete transfers are deducted from the sender's AND added to the recipient's
    """
    sta = new_credit_transfer.sender_transfer_account
    rta = new_credit_transfer.recipient_transfer_account

    sta.set_balance_offset(10000)
    rta.set_balance_offset(10000)

    assert sta.balance == 9000
    assert rta.balance == 10000

    new_credit_transfer.resolve_as_complete()

    assert sta.balance == 9000
    assert rta.balance == 11000

def test_balance_handles_partial_statuses(new_credit_transfer):
    """
    Make sure that pending transfers are deducted from the sender's balance, but NOT added to the recipient's,
    while complete transfers are deducted from the sender's AND added to the recipient's
    """
    sta = new_credit_transfer.sender_transfer_account
    rta = new_credit_transfer.recipient_transfer_account
    # Set initial balances
    sta.set_balance_offset(10000)
    rta.set_balance_offset(10000)
    # Check balance correctness after updated in PENDING state
    # Sent funds should be inaccessible from senders' account, but not yet in recipient's account
    new_credit_transfer.transfer_status = 'PENDING'
    rta.update_balance()
    sta.update_balance()
    assert sta.balance == 9000
    assert rta.balance == 10000

    assert sta.total_sent_complete_only_wei == 0
    assert rta.total_sent_complete_only_wei == 0

    assert sta.total_received_complete_only_wei == 0
    assert rta.total_received_complete_only_wei == 0
    
    assert sta.total_sent_incl_pending_wei == 10000000000000000000
    assert rta.total_sent_incl_pending_wei == 0

    assert sta.total_received_incl_pending_wei == 0
    assert rta.total_received_incl_pending_wei == 10000000000000000000

    # Check balance correctness after updated in PARTIAL state (no change from PENDING)
    new_credit_transfer.transfer_status = 'PARTIAL'
    rta.update_balance()
    sta.update_balance()
    assert sta.balance == 9000
    assert rta.balance == 10000

    assert sta.total_sent_complete_only_wei == 0
    assert rta.total_sent_complete_only_wei == 0

    assert sta.total_received_complete_only_wei == 0
    assert rta.total_received_complete_only_wei == 0

    assert sta.total_sent_incl_pending_wei == 10000000000000000000
    assert rta.total_sent_incl_pending_wei == 0

    assert sta.total_received_incl_pending_wei == 0
    assert rta.total_received_incl_pending_wei == 10000000000000000000

    # When COMPLETE, the 100 should be out of sender AND in rta
    new_credit_transfer.transfer_status = 'COMPLETE'
    rta.update_balance()
    sta.update_balance()
    assert sta.balance == 9000
    assert rta.balance == 11000

    assert sta.total_sent_complete_only_wei == 10000000000000000000
    assert rta.total_sent_complete_only_wei == 0

    assert sta.total_received_complete_only_wei == 0
    assert rta.total_received_complete_only_wei == 10000000000000000000
    
    assert sta.total_sent_incl_pending_wei == 10000000000000000000
    assert rta.total_sent_incl_pending_wei == 0

    assert sta.total_received_incl_pending_wei == 0
    assert rta.total_received_incl_pending_wei == 10000000000000000000

def test_total_sent_amounts(new_credit_transfer):
    """
    Test the total sent amounts account for pending/complete state changes appropriately
    """
    ta = new_credit_transfer.sender_transfer_account

    assert ta.total_sent_incl_pending_wei == 10000000000000000000
    assert ta.total_sent_complete_only_wei == 0

    new_credit_transfer.resolve_as_complete()

    assert ta.total_sent_incl_pending_wei == 10000000000000000000
    assert ta.total_sent_complete_only_wei == 10000000000000000000

def test_total_received_amounts(new_credit_transfer):
    """
    Test the total received amounts account for pending/complete state changes appropriately

    """

    ta = new_credit_transfer.recipient_transfer_account

    assert ta.total_received_incl_pending_wei == 10000000000000000000
    assert ta.total_received_complete_only_wei == 0

    new_credit_transfer.resolve_as_complete()

    assert ta.total_received_incl_pending_wei == 10000000000000000000
    assert ta.total_received_complete_only_wei == 10000000000000000000

