import pytest
from server.utils import credit_transfer as CreditTransferUtils
from server.exceptions import (
    UserNotFoundError,
    NoTransferAccountError,
    AccountNotApprovedError,
    InsufficientBalanceError
)


def test_cents_to_dollars():
    assert CreditTransferUtils.cents_to_dollars(100) == 1


def tets_dollars_to_cents():
    assert CreditTransferUtils.dollars_to_cents(1) == 100


def test_find_user_with_transfer_account_from_identifiers_error(test_client, init_database, create_master_organisation,
                                                                new_sempo_admin_user):
    with pytest.raises(NoTransferAccountError):
        CreditTransferUtils.find_user_with_transfer_account_from_identifiers(new_sempo_admin_user.id, None, None)


@pytest.mark.parametrize("user_id, public_identifier, transfer_account_id", [
    (11, None, None),
    (None, '1111', None),
    (None, '1111', 5),
])
def test_find_user_from_identifiers_errors(test_client, init_database, create_master_organisation, user_id,
                                           public_identifier, transfer_account_id):
    with pytest.raises(UserNotFoundError):
        CreditTransferUtils.find_user_from_identifiers(user_id, public_identifier, transfer_account_id)


@pytest.mark.parametrize(
    "transfer_amount, require_sender_approved, require_recipient_approved, require_sufficient_balance, error", [
        (10, True, None, None, AccountNotApprovedError),
        (10, None, True, None, AccountNotApprovedError),
        (10, False, False, True, InsufficientBalanceError),
    ])
def test_make_payment_transfer_error(test_client, init_database, create_transfer_account_user,
                                     create_user_with_existing_transfer_account, transfer_amount,
                                     require_sender_approved, require_recipient_approved, require_sufficient_balance,
                                     error):
    send_user = create_transfer_account_user
    if require_sender_approved:
        send_user.transfer_account.is_approved = False

    receive_user = create_user_with_existing_transfer_account
    if require_recipient_approved:
        receive_user.transfer_account.is_approved = False

    with pytest.raises(error):
        CreditTransferUtils.make_payment_transfer(
            transfer_amount=transfer_amount,
            token=send_user.transfer_account.token,
            send_user=send_user,
            receive_user=receive_user,
            require_sender_approved=require_sender_approved,
            require_recipient_approved=require_recipient_approved,
            require_sufficient_balance=require_sufficient_balance,
        )
