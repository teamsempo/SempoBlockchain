"""
This file (test_phone.py) contains the unit tests for the phone.py file in utils dir.
"""
import pytest

@pytest.mark.parametrize("phone,expected, region", [
    ("0401391419", "+61401391419", 'AU'),
    ("0401391419", "+61401391419", None),
    ("0401391419", "+961401391419", 'LB'),
    ("+961401391419", "+961401391419", 'AU'),
])
def test_proccess_phone_number(proccess_phone_number_with_ctx, phone, expected, region):
    """
    GIVEN proccess_phone_number function
    WHEN called with a phone_number WITHOUT and WITH country code
    THEN check that default country code is added if required
    """
    assert proccess_phone_number_with_ctx(phone, region) == expected
