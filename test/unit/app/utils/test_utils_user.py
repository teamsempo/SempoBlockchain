"""
This file (test_utils_user.py) contains the unit tests for the user.py file in utils dir.
"""
from functools import partial

import pytest
import config
from flask import g

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
from helpers.factories import UserFactory, OrganisationFactory, TokenFactory, TransferAccountFactory, fake
from server.models.user import RegistrationMethodEnum
from server.utils.user import transfer_usages_for_user
from server.utils.user import admin_reset_user_pin
from server.utils.user import proccess_create_or_modify_user_request
from server.utils.user import send_onboarding_sms_messages
from server.utils.user import attach_transfer_account_to_user
from server import db


@pytest.mark.parametrize("last_name, location, lat, lng, initial_disbursement", [
    ('Hound', 'Melbourne, Victoria Australia', -37.8104277, 144.9629153, 400),
    ('Hound', 'Melbourne, Victoria Australia', None, None, 400),
    ('Hound', None, -37.8104277, 144.9629153, 400),
    (None, None, None, None, None)
])
def test_create_transfer_account_user(
        test_client, init_database, create_master_organisation,
        last_name, location, lat, lng, initial_disbursement):
    from flask import g
    g.active_organisation = create_master_organisation

    assert proccess_create_or_modify_user_request(
        attribute_dict=dict(
        first_name='Lilly', last_name=last_name,
        phone=fake.msisdn(),
        location=location, lat=lat, lng=lng,
        initial_disbursement=initial_disbursement))


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


def test_admin_reset_user_pin(mocker, test_client, init_database, create_transfer_account_user):
    send_message = mocker.MagicMock()
    mocker.patch('server.message_processor.send_message', send_message)

    user = create_transfer_account_user
    admin_reset_user_pin(user)

    assert user.failed_pin_attempts == 0
    assert isinstance(user.pin_reset_tokens, list)
    assert len(user.pin_reset_tokens) == 1

    send_message.assert_has_calls([mocker.call(user.phone, 'Dial *483*46# to change your PIN')])


@pytest.mark.parametrize("preferred_language, org_key, expected_welcome, expected_terms", [

    (None, None,
     'Hello Magoo, you have been registered on Sempo! Your balance is 100.00 Sarafu.',
     'By using the service, you agree to the terms and conditions at https://www.grassrootseconomics.org/terms-and-conditions.'),

    (None, "grassroots",
     'Hello Magoo you have been registered on Sarafu Network! Your balance is 100.00 Sarafu. To use dial *483*46#. For help 0757628885',
     'By using the service, you agree to the terms and conditions at https://www.grassrootseconomics.org/terms-and-conditions.'),

    ('sw', None,
     'Habari Magoo, umesajiliwa kwa Sempo! Salio yako ni 100.00 Sarafu.',
     'Kwa kutumia hii huduma, umekubali sheria na masharti yafuatayo https://www.grassrootseconomics.org/terms-and-conditions.'),

    ('sw', 'grassroots',
     'Habari Magoo, umesajiliwa kwa huduma ya sarafu! Salio lako ni Sarafu 100.00. Kutumia bonyeza *483*46#. Kwa Usaidizi 0757628885',
     'Kwa kutumia hii huduma, umekubali sheria na masharti yafuatayo https://www.grassrootseconomics.org/terms-and-conditions.'),

])
def test_send_welcome_sms(mocker, test_client, init_database,
                          preferred_language, org_key, expected_welcome, expected_terms):
    from flask import g

    token = TokenFactory(name='Sarafu', symbol='SARAFU')
    organisation = OrganisationFactory(custom_welcome_message_key=org_key, token=token, country_code='AU')
    g.active_organisation = organisation
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


def test_attach_transfer_account_to_user(test_client, init_database, create_organisation):
    with db.session.no_autoflush:
        organisation = create_organisation
        organisation.external_auth_password = config.EXTERNAL_AUTH_PASSWORD

        g.active_organisation = organisation

        user = UserFactory(id=20,
                           phone='+61756432178',
                           first_name='Unknown first name',
                           last_name='Unknown last name',
                           registration_method=RegistrationMethodEnum.USSD_SIGNUP)

        user.add_user_to_organisation(organisation, False)

        assert user.primary_blockchain_address is None

        user_with_transfer_account = attach_transfer_account_to_user(user)

        assert user_with_transfer_account.primary_blockchain_address is not None
        bio = next(filter(lambda x: x.name == 'bio', user_with_transfer_account.custom_attributes), None)
        assert bio.value.strip('"') == 'Unknown business'
        gender = next(filter(lambda x: x.name == 'gender', user_with_transfer_account.custom_attributes), None)
        assert gender.value.strip('"') == 'Unknown gender'
        assert user_with_transfer_account.location == 'Unknown location'
