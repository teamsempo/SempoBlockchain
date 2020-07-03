import pytest


def test_create_transfer_account(create_transfer_account):
    """
    GIVEN A transfer account model
    WHEN a new transfer account is created
    THEN check a blockchain address is created, default balance is 0
    """
    assert create_transfer_account.balance == 0
    assert create_transfer_account.blockchain_address is not None


def test_approve_beneficiary_transfer_account(create_transfer_account_user, create_organisation):
    """
    GIVEN a Transfer Account model
    WHEN a new transfer account is created AND approved
    THEN check a BENEFICIARY is disbursed initial balance
    """
    create_transfer_account_user.transfer_account.is_beneficiary = True
    create_transfer_account_user.transfer_account.approve_and_disburse(
        initial_disbursement=create_organisation.default_disbursement
    )

    assert create_transfer_account_user.transfer_account.balance == create_organisation.default_disbursement


def test_approve_vendor_transfer_account(create_transfer_account_user):
    """
    GIVEN a Transfer Account model
    WHEN a new transfer account is created and approved
    THEN check a VENDOR is NOT disbursed initial balance
    """
    create_transfer_account_user.transfer_account.is_beneficiary = False

    create_transfer_account_user.transfer_account.is_vendor = True
    create_transfer_account_user.transfer_account.approve_and_disburse()

    assert create_transfer_account_user.transfer_account.balance == 400
