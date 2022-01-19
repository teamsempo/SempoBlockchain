import pytest
from uuid import uuid4
from flask import g
from server.utils.transfer_enums import TransferStatusEnum


from helpers.model_factories import TransferAccountFactory, CreditTransferFactory, TokenFactory, OrganisationFactory

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


u1 = '20545fb2-d63f-4e92-bc06-318160bc7bfe'
u2 = 'bono'
u3 = '52eed2eb-af79-49f3-ad47-9eb9fd37bbb1'

def test_prior_task_requirements(test_client, init_database):
    """
    Test whether the calculated submission order for a set of transactions is what we expect it to be
    ie one that prevents an unrecoverable state from being reached
    """

    token = TokenFactory(name='SempoBucks', symbol='SempoBucks')
    organisation = OrganisationFactory(token=token, country_code='AU')
    g.active_organisation = organisation
    ta1 = TransferAccountFactory(token=token, organisation=organisation)
    ta2 = TransferAccountFactory(token=token, organisation=organisation)
    ta3 = TransferAccountFactory(token=token, organisation=organisation)

    # First start with a plain transfer from ta1 to ta2
    send1 = CreditTransferFactory(
        amount=1000,
        sender_transfer_account=ta1,
        recipient_transfer_account=ta2,
        require_sufficient_balance=False
    )

    send1.transfer_status = TransferStatusEnum.COMPLETE

    # Make sure that get prior tasks doesn't pick up its
    assert send1._get_required_prior_tasks() == set()

    init_database.session.commit()
    # Test with and without commit
    assert send1._get_required_prior_tasks() == set()

    # Same sender/recipient as original.
    send2 = CreditTransferFactory(
        amount=1000,
        sender_transfer_account=ta1,
        recipient_transfer_account=ta2,
        require_sufficient_balance=False
    )

    # Should pick up prior send.
    assert send2._get_required_prior_tasks() == {send1}

    # send1's batch shouldn't make a difference yet
    send1.batch_uuid = u1
    assert send2._get_required_prior_tasks() == {send1}

    # different batch ID shouldn't make a difference either
    send2.batch_uuid = u2
    assert send2._get_required_prior_tasks() == {send1}

    # Now send1 shouldn't be included as a prior requirement, because it's the same batch
    send2.batch_uuid = u1
    assert send2._get_required_prior_tasks() == set()

    # Now ta1 is receiving
    receive1 = CreditTransferFactory(
        amount=1000,
        sender_transfer_account=ta3,
        recipient_transfer_account=ta1,
        require_sufficient_balance=False
    )

    receive2 = CreditTransferFactory(
        amount=1000,
        sender_transfer_account=ta3,
        recipient_transfer_account=ta1,
        require_sufficient_balance=False
    )

    send3 = CreditTransferFactory(
        amount=1000,
        sender_transfer_account=ta1,
        recipient_transfer_account=ta2,
        require_sufficient_balance=False
    )

    # Should just be send1, as send2, receive1 and receive2 aren't resolved as complete yet
    assert send3._get_required_prior_tasks() == {send1}

    send2.batch_uuid = None
    send2.transfer_status = TransferStatusEnum.COMPLETE
    receive1.transfer_status = TransferStatusEnum.COMPLETE
    receive2.transfer_status = TransferStatusEnum.COMPLETE

    # Now send1 should be excluded because the dependency is implicit from send2
    assert send3._get_required_prior_tasks() == {receive2, receive1, send2}

    send3.transfer_status = TransferStatusEnum.COMPLETE

    assert send3._get_required_prior_tasks() == {receive2, receive1, send2}

    send4 = CreditTransferFactory(
        amount=1000,
        sender_transfer_account=ta1,
        recipient_transfer_account=ta2,
        require_sufficient_balance=False
    )

    send5 = CreditTransferFactory(
        amount=1000,
        sender_transfer_account=ta1,
        recipient_transfer_account=ta2,
        require_sufficient_balance=False
    )

    send3.batch_uuid = u3
    send4.batch_uuid = u3
    send5.batch_uuid = u3

    assert send3._get_required_prior_tasks() == {receive2, receive1, send2}

    # big batch
    assert send5._get_required_prior_tasks() == {receive2, receive1, send2}

    send3.transfer_status = TransferStatusEnum.COMPLETE
    send4.transfer_status = TransferStatusEnum.COMPLETE
    send5.transfer_status = TransferStatusEnum.COMPLETE

    send6 = CreditTransferFactory(
        amount=1000,
        sender_transfer_account=ta1,
        recipient_transfer_account=ta2,
        require_sufficient_balance=False
    )

    assert send6._get_required_prior_tasks() == {send3, send4, send5}





