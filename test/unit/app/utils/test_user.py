"""
This file (test_user.py) contains the unit tests for the user.py file in utils dir.
"""
import pytest
from functools import partial
from helpers.user import UserFactory
from faker.providers import phone_number
from faker import Faker
from server.utils import user
from server.utils.user import change_initial_pin, change_current_pin


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


fake = Faker()
fake.add_provider(phone_number)
phone = partial(fake.msisdn)
unactivated_user = partial(UserFactory, is_activated=False)
standard_user = partial(UserFactory, pin='0000')


@pytest.mark.parametrize("user_factory, user_input, expected_new_pin, expected_activation_status",
                         [(unactivated_user, "0000", "0000", True)])
def test_change_initial_pin(mocker, test_client, init_database, user_factory, user_input, expected_new_pin,
                            expected_activation_status):
    ua_user = user_factory()
    ua_user.phone = phone()
    assert ua_user.pin is None
    assert ua_user.is_activated is False

    user.send_sms = mocker.MagicMock()
    change_initial_pin(ua_user, user_input)

    assert ua_user.verify_pin(expected_new_pin) is True
    assert ua_user.is_activated is expected_activation_status
    user.send_sms.assert_called_with(ua_user, 'successful_pin_change_sms')


@pytest.mark.parametrize("user_factory, user_input, expected_new_pin",
                         [(standard_user, "1111", "1111")])
def test_change_current_pin(mocker, user_factory, user_input, expected_new_pin):
    strd_user = user_factory()
    strd_user.phone = phone()
    assert strd_user.verify_pin('0000') is True

    user.send_sms = mocker.MagicMock()
    change_current_pin(strd_user, user_input)

    assert strd_user.verify_pin(expected_new_pin) is True
    user.send_sms.assert_called_with(strd_user, 'successful_pin_change_sms')
