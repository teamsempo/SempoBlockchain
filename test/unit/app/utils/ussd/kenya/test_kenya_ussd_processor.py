import pytest
from functools import partial

from helpers.ussd_utils import fake_transfer_mapping
from server.utils.ussd.kenya_ussd_processor import KenyaUssdProcessor

from helpers.user import UserFactory, TransferUsageFactory
from helpers.ussd_session import UssdSessionFactory, UssdMenuFactory
from server import db
from server.utils.ussd.kenya_ussd_state_machine import KenyaUssdStateMachine

standard_user = partial(UserFactory)



def mock_transfer_usages_for_user():
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


@pytest.mark.parametrize("menu_name, language, expecteds, real_at_idx, length, unexpected, menu_nr", [
    ("send_token_reason", "en", ['\n1. Education\n2. Health', "9."], 0, 12, "10.", 0),
    ("send_token_reason", "sw", ['\n1. Elimu\n2. Afya', "9."], 0, 12, "10.", 0),
    ("send_token_reason", None, ['\n1. Education\n2. Health', "9."], 0, 12, "10.", 0),
    # first
    ("send_token_reason_other", "en", ['\n1. Education\n2. Health', "9."], 0, 12, "10.", 0),
    # last
    ("send_token_reason_other", "en", ['\n1. Education\n2. Health', "10."], 8, 12, "9.", 1),
    ("send_token_reason_other", "sw", ['\n1. Elimu\n2. Afya', "10."], 8, 12, "9.", 1),
    # middle
    ("send_token_reason_other", "en", ['\n1. Education\n2. Health', "9.", "10."], 8, 20, None, 1),
    ("directory_listing", "en", ['\n1. Education\n2. Health', "9."], 0, 12, "10.", 0),
    ("directory_listing", "sw", ['\n1. Elimu\n2. Afya', "9."], 0, 12, "10.", 0),
    ("directory_listing", None, ['\n1. Education\n2. Health', "9."], 0, 12, "10.", 0),
    # first
    ("directory_listing_other", "en", ['\n1. Education\n2. Health', "9."], 0, 12, "10.", 0),
    # last
    ("directory_listing_other", "en", ['\n1. Education\n2. Health', "10."], 8, 12, "9.", 1),
    ("directory_listing_other", "sw", ['\n1. Elimu\n2. Afya', "10."], 8, 12, "9.", 1),
    # middle
    ("directory_listing_other", "en", ['\n1. Education\n2. Health', "9.", "10."], 8, 20, None, 1)
])
def test_custom_display_text(test_client, init_database, menu_name, language, expecteds,
                             real_at_idx, length, unexpected, menu_nr):
    with db.session.no_autoflush:
        start_state = UssdSessionFactory()

        mapping = fake_transfer_mapping(length)
        real_usage1 = TransferUsageFactory(name='Education', id=2, default=True)
        real_usage1.translations = {'en': 'Education', 'sw': 'Elimu'}
        real_usage2 = TransferUsageFactory(name='Health', id=2, default=True)
        real_usage2.translations = {'en': 'Health', 'sw': 'Afya'}
        mapping[real_at_idx] = KenyaUssdStateMachine.make_usage_mapping(real_usage1)
        mapping[real_at_idx + 1] = KenyaUssdStateMachine.make_usage_mapping(real_usage2)
        start_state.session_data = {'transfer_usage_mapping': mapping, 'usage_menu': menu_nr}

        user = standard_user()
        user.preferred_language = language

        menu = UssdMenuFactory(name=menu_name, display_key="ussd.kenya.{}".format(menu_name))
        resulting_menu = KenyaUssdProcessor.custom_display_text(
            menu, start_state, user)

        for expected in expecteds:
            assert expected in resulting_menu
        if unexpected is not None:
            assert unexpected not in resulting_menu
