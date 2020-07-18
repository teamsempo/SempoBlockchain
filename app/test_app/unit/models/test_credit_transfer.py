import pytest

def test_new_credit_transfer_complete(create_credit_transfer):
    """
    GIVEN a CreditTransfer model
    WHEN a new credit transfer is created
    THEN check transfer status is PENDING, then resolve as complete
    """
    from server.utils.transfer_enums import TransferStatusEnum
    from flask import g
    g.pending_transactions = []
    assert isinstance(create_credit_transfer.transfer_amount, float)
    assert create_credit_transfer.transfer_amount == 1000
    assert create_credit_transfer.transfer_status is TransferStatusEnum.PENDING
    create_credit_transfer.resolve_as_complete_and_trigger_blockchain()  # complete credit transfer
    assert create_credit_transfer.transfer_status is TransferStatusEnum.COMPLETE

    with pytest.raises(Exception):
        assert create_credit_transfer.resolve_as_complete_and_trigger_blockchain()


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

    with pytest.raises(Exception):
        assert create_credit_transfer.resolve_as_rejected()