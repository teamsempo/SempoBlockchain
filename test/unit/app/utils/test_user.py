"""
This file (test_user.py) contains the unit tests for the user.py file in utils dir.
"""
import pytest


# REDACTED: USERS NOW HAVE MULTIPLE TRANSFER ACCOUNTS
# def test_create_transfer_account_user(create_transfer_account_user):
#     """
#     GIVEN create_transfer_account_user function
#     WHEN called with first_name, last_name, phone
#     THEN assert one_time_code, transfer account exists,
#         transfer_account approval is equal to config
#     """
#     import config
#     assert create_transfer_account_user.one_time_code is not None
#     assert create_transfer_account_user.transfer_account is not None
#     assert create_transfer_account_user.transfer_account.is_approved is config.AUTO_APPROVE_TRANSFER_ACCOUNTS


def test_create_user_with_existing_transfer_account(create_user_with_existing_transfer_account, create_transfer_account):
    """
    GIVEN create_transfer_account_user function
    WHEN called with first_name, last_name, phone AND existing transfer account
    THEN assert transfer account tied to user object
    """
    assert create_user_with_existing_transfer_account.transfer_account is create_transfer_account


@pytest.mark.parametrize("serial_number,unique_id", [
    ("wHaTaRaNdOmSeRiAlNuMbEr", '5'),
    (None, '12'),
])
def test_save_device_info(save_device_info, new_sempo_admin_user, serial_number, unique_id):
    """
    GIVEN save_device_info function
    WHEN called with device_info and user object
    THEN assert device info is saved
    """
    from server import db
    device = save_device_info(
        device_info=dict(
            serialNumber=serial_number,
            uniqueId=unique_id,
            model=None,
            brand=None,
            width=None,
            height=None
        ),
        user=new_sempo_admin_user
    )
    db.session.commit()
    assert device is not None
    assert device.user_id is new_sempo_admin_user.id

