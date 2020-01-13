import pytest


def test_create_transfer_account(create_transfer_account):
    """
    GIVEN A transfer account model
    WHEN a new transfer account is created
    THEN check a blockchain address is created, default balance is 0
    """
    assert create_transfer_account.balance == 0
    assert create_transfer_account.blockchain_address is not None


def test_approve_beneficiary_transfer_account(create_transfer_account_user):
    """
    GIVEN a Transfer Account model
    WHEN a new transfer account is created AND approved
    THEN check a BENEFICIARY is disbursed initial balance
    """
    import config
    create_transfer_account_user.transfer_account.is_beneficiary = True
    create_transfer_account_user.transfer_account.approve_and_disburse()

    assert create_transfer_account_user.transfer_account.balance == config.DEFAULT_INITIAL_DISBURSEMENT


def test_approve_vendor_transfer_account(new_transfer_account):
    """
    GIVEN a Transfer Account model
    WHEN a new transfer account is created and approved
    THEN check a VENDOR is NOT disbursed initial balance
    """
    new_transfer_account.is_vendor = True
    new_transfer_account.approve_and_disburse()

    assert new_transfer_account.balance == 0


@pytest.mark.parametrize("initial_bal, increment_amount, expected_final_bal", [
    (0, 0.0, 0.0),
    (5, 0.5, 5.5),
    (0.1, 0.00001, 0.10001),
    (0, -0.0, 0.0),
    (5, -0.5, 4.5),
    (0.1, - 0.00001, 0.09999),
])
def test_increment_balance(test_client, init_database, create_master_organisation,
                           initial_bal, increment_amount, expected_final_bal):
    """
    Tests to ensure that adding and subtracting floats doesn't destroy decimal amounts, esp after db commit
    """
    import server.models.transfer_account
    from server import db
    ta = server.models.transfer_account.TransferAccount()
    ta.balance = initial_bal
    db.session.add(ta)
    db.session.commit()
    id = ta.id
    db.session.expire(ta)

    ta_queried = server.models.transfer_account.TransferAccount.query.execution_options(show_all=True).get(id)

    ta_queried.increment_balance(increment_amount)

    assert ta_queried.balance == expected_final_bal


@pytest.mark.parametrize("initial_bal, decrement_amount, expected_final_bal", [
    (0, 0.0, 0.0),
    (5, 0.5, 4.5),
    (0.1, 0.00001, 0.09999),
    (0, -0.0, 0.0),
    (5, -0.5, 5.5),
    (0.1, - 0.00001, 0.10001),
])
def test_decrement_balance(test_client, init_database, create_master_organisation,
                           initial_bal, decrement_amount, expected_final_bal):
    """
    Tests to ensure that adding and subtracting floats doesn't destroy decimal amounts, esp after db commit
    """
    import server.models.transfer_account
    from server import db
    ta = server.models.transfer_account.TransferAccount()
    ta.balance = initial_bal
    db.session.add(ta)
    db.session.commit()
    id = ta.id
    db.session.expire(ta)

    ta_queried = server.models.transfer_account.TransferAccount.query.execution_options(show_all=True).get(id)

    ta_queried.decrement_balance(decrement_amount)

    assert ta_queried.balance == expected_final_bal