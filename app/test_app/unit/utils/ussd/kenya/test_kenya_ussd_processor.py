import pytest
from functools import partial

from helpers.utils import fake_transfer_mapping
from server.models.transfer_usage import TransferUsage
from server.models.ussd import UssdMenu
from server.utils.ussd.ussd_processor import UssdProcessor

from helpers.model_factories import UserFactory, UssdSessionFactory
from server import db
from server.utils.ussd.ussd_state_machine import UssdStateMachine

standard_user = partial(UserFactory)


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
        start_state = UssdSessionFactory(state="menu_name")

        mapping = fake_transfer_mapping(length)
        real_usage1 = TransferUsage.find_or_create('Education')
        real_usage1.translations = {'en': 'Education', 'sw': 'Elimu'}
        real_usage2 = TransferUsage.find_or_create('Health')
        real_usage2.translations = {'en': 'Health', 'sw': 'Afya'}
        mapping[real_at_idx] = UssdStateMachine.make_usage_mapping(real_usage1)
        mapping[real_at_idx + 1] = UssdStateMachine.make_usage_mapping(real_usage2)
        user = standard_user()
        user.preferred_language = language

        start_state.session_data = {
            'transfer_usage_mapping': mapping,
            'usage_menu': menu_nr,
            'usage_index_stack': [0, 8]
        }

        start_state.user = user

        menu = UssdMenu(name=menu_name, display_key="ussd.sempo.{}".format(menu_name))
        resulting_menu = UssdProcessor.custom_display_text(
            menu, start_state)

        for expected in expecteds:
            assert expected in resulting_menu
        if unexpected is not None:
            assert unexpected not in resulting_menu
