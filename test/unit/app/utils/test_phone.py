"""
This file (test_phone.py) contains the unit tests for the phone.py file in utils dir.
"""
import pytest


@pytest.mark.parametrize("phone,expected", [
    ("0401391419", "+61401391419"),
    ("+12020000000", "+12020000000"),
])
def test_proccess_phone_number(proccess_phone_number, phone, expected):
    """
    GIVEN proccess_phone_number function
    WHEN called with a phone_number WITHOUT and WITH country code
    THEN check that default country code is added if required
    """
    assert proccess_phone_number(phone) == expected
