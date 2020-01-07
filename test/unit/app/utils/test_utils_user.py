"""
This file (test_utils_user.py) contains the unit tests for the user.py file in utils dir.
"""
from functools import partial

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
from helpers.factories import UserFactory, OrganisationFactory, TokenFactory, TransferAccountFactory
from server.utils.user import transfer_usages_for_user, send_onboarding_sms_messages


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


def test_transfer_usages_for_user(authed_sempo_admin_user):
    """
    GIVEN A User Model
    WHEN transfer_usages_for_user is called
    THEN a list is returned
    """
    # TODO This test in pretty lightweight atm it just checks if a list - also test if it sorts correctly:
    # first by highest count
    # then by defaults
    # then by everything else
    # can mock out relevant_usage call for a list
    usages = transfer_usages_for_user(authed_sempo_admin_user)
    assert isinstance(usages, list)



@pytest.mark.parametrize("preferred_language, org_key, expected_welcome, expected_terms", [

    (None, None,
     'Hello Magoo, you have been registered on Sempo! Your balance is 100.00 Sarafu.',
     'By using the service, you agree to the terms and conditions at https://withsempo.com/legal.'),

    (None, "grassroots",
     'Hello Magoo you have been registered on Sarafu Network! Your balance is 100.00 Sarafu. To use dial *384*96# Safaricom or *483*46# Airtel. For help 0757628885',
     'By using the service, you agree to the terms and conditions at https://withsempo.com/legal.'),

    ('sw', None,
     'Habari Magoo, umesajiliwa kwa Sempo! Salio yako ni 100.00 Sarafu.',
     'Kwa kutumia hii huduma, umekubali sheria na masharti yafuatayo https://withsempo.com/legal.'),

    ('sw', 'grassroots',
     'Habari Magoo, umesajiliwa kwa huduma ya sarafu! Salio lako ni Sarafu 100.00. Kutumia bonyeza *384*96# kwa Safaricom au *483*46# Airtel. Kwa Usaidizi 0757628885',
     'Kwa kutumia hii huduma, umekubali sheria na masharti yafuatayo https://withsempo.com/legal.'),

])
def test_send_welcome_sms(mocker, test_client, init_database,
                          preferred_language, org_key, expected_welcome, expected_terms):

    token = TokenFactory(name='Sarafu', symbol='SARAFU')
    organisation = OrganisationFactory(custom_welcome_message_key=org_key, token=token)
    transfer_account = TransferAccountFactory(balance=10000, token=token, organisation=organisation)
    user = UserFactory(first_name='Magoo',
                       phone='123456789',
                       preferred_language=preferred_language,
                       organisations=[organisation],
                       default_organisation=organisation,
                       transfer_accounts=[transfer_account])

    send_message = mocker.MagicMock()
    mocker.patch('server.message_processor.send_message', send_message)

    send_onboarding_sms_messages(user)

    send_message.assert_has_calls(
        [mocker.call('+61123456789', expected_welcome),
         mocker.call('+61123456789', expected_terms)])

