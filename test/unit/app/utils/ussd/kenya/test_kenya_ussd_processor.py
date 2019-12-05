import pytest
from functools import partial
from server.utils.ussd.kenya_ussd_processor import KenyaUssdProcessor

from helpers.user import UserFactory, TransferUsageFactory
from helpers.ussd_session import UssdSessionFactory, UssdMenuFactory
from server import db
standard_user = partial(UserFactory)



def mock_get_most_relevant_transfer_usage():
    transfer_usage_1 = partial(TransferUsageFactory)
    transfer_usage_1.id = 1
    transfer_usage_1.name = 'Food'
    transfer_usage_1.translations = {'en': 'Food', 'sw': 'Chakula'}
    transfer_usage_2 = partial(TransferUsageFactory)
    transfer_usage_2.id = 2
    transfer_usage_2.translations = {'en': 'Education', 'sw': 'Elimu'}
    transfer_usage_2.name = 'Education'
    list_of_transfer_usage = [transfer_usage_1, transfer_usage_2]
    return list_of_transfer_usage


@pytest.mark.parametrize("menu_name, language, expected", [
    ("send_token_reason", "en", '\n1. Food\n2. Education'),
    ("send_token_reason", "sw", '\n1. Chakula\n2. Elimu'),
    ("send_token_reason", None, '\n1. Food\n2. Education'),
    ("directory_listing", "en", '\n1. Food\n2. Education'),
    ("directory_listing", "sw", '\n1. Chakula\n2. Elimu'),
    ("directory_listing", None, '\n1. Food\n2. Education'),
])
def test_custom_display_text(mocker, test_client, init_database, menu_name, language, expected):
    transferUsage = TransferUsageFactory(name='Food', id=1, default=True)
    transferUsage2 = TransferUsageFactory(name='Education', id=2, default=True)
    
    with db.session.no_autoflush:
        start_state = UssdSessionFactory()
        # start_state = UssdSessionFactory(session_data={'transfer_usage_mapping': [1]})
        start_state.session_data = {'transfer_usage_mapping': [1, 2]}
        user = standard_user()
        user.preferred_language = language

        # type(user).get_most_relevant_transfer_usage = mocker.PropertyMock(
        #     return_value=mock_get_most_relevant_transfer_usage)
        menu = UssdMenuFactory(name=menu_name, display_key="ussd.kenya.{}".format(menu_name))
        resulting_menu = KenyaUssdProcessor.custom_display_text(
            menu, start_state, user)

        assert expected in resulting_menu
