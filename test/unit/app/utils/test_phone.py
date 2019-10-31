"""
This file (test_phone.py) contains the unit tests for the phone.py file in utils dir.
"""
import pytest

from server.utils.phone import ChannelType


@pytest.fixture(scope='function')
def proccess_phone_number(test_client):
    from server.utils.phone import proccess_phone_number
    return proccess_phone_number

@pytest.fixture(scope='function')
def channel_for_number(test_client):
    from server.utils.phone import channel_for_number
    return channel_for_number

@pytest.mark.parametrize("phone,region,expected", [
    ("0401391419", None, "+61401391419"),
    ("+961401391419", None, "+961401391419"),
    ("0401391419", "KE", "+254401391419"),
])
def test_proccess_phone_number(proccess_phone_number, phone, region, expected):
    """
    GIVEN proccess_phone_number function
    WHEN called with a phone_number WITHOUT and WITH country code
    THEN check that default country code is added if required
    """
    assert proccess_phone_number(phone, region) == expected

@pytest.mark.parametrize("phone,expected", [
    ("+1401391419", ChannelType.TWILIO),
    ("+961401391419", ChannelType.TWILIO),
    ("+254796918514", ChannelType.AFRICAS_TALKING),
])
def test_channel_for_number(channel_for_number, phone, expected):
    assert channel_for_number(phone) == expected
