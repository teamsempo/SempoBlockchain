import pytest
from server.exceptions import IconNotSupportedException

def test_create_transfer_usage(create_transfer_usage):
    """
    GIVEN a TransferUsage Model
    WHEN a new Transfer Usage is created
    THEN check id, created, name, icon, translations
    """
    assert isinstance(create_transfer_usage.id, int)
    assert isinstance(create_transfer_usage.created, object)

    assert create_transfer_usage.name == 'Food'
    assert create_transfer_usage.icon == 'food-apple'
    assert create_transfer_usage.translations == dict(en='Food', fr='aliments')


def test_create_transfer_usage_exception(create_transfer_usage):
    """
    GIVEN a TransferUsage Model
    WHEN a new Transfer Usage is created and the icon is not supported
    THEN check the IconNotSupportedException is raised
    """
    with pytest.raises(IconNotSupportedException):
        create_transfer_usage.icon = 'bananaaaas'
