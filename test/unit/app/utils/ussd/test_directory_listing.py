import pytest
from functools import partial
from faker.providers import phone_number
from faker import Faker

from helpers.user import UserFactory
from server.utils.ussd.directory_listing import DirectoryListingProcessor
from server.models.transfer_account import TransferAccount

fake = Faker()
fake.add_provider(phone_number)
phone = partial(fake.msisdn)


@pytest.fixture(scope='function')
def dl_processor(create_transfer_account_user, create_transfer_usage):
    return DirectoryListingProcessor(create_transfer_account_user, create_transfer_usage)


def test_get_directory_listing_users(test_client, init_database, dl_processor):
    user = dl_processor.recipient
    # TODO: test market_enabled=false doesn't show up
    # TODO: test only shows ones from same token / business category
    # TODO: test ordered by highest transaction count



def test_get_business_category_translation(test_client, init_database, dl_processor):
    cat = dl_processor.selected_business_category
    assert cat.translations['fr'] is not None
    with pytest.raises(KeyError):
        cat.translations['sw']

    user = dl_processor.recipient
    assert user.preferred_language is None

    assert dl_processor.get_business_category_translation() == cat.name

    user.preferred_language = 'sw'
    assert dl_processor.get_business_category_translation() == cat.name

    user.preferred_language = 'fr'
    assert dl_processor.get_business_category_translation() == cat.translations['fr']


def test_send_directory_listing(mocker, test_client, init_database, dl_processor):
    user = dl_processor.recipient
    transfer_account = TransferAccount.query.get(user.default_transfer_account_id)
    transfer_account.token.name = "A Token"

    # TODO: add bio
    user1 = UserFactory(phone=phone())
    user2 = UserFactory(phone=phone())
    dl_processor.get_directory_listing_users = mocker.MagicMock(return_value=[user1, user2])
    dl_processor.get_business_category_translation = mocker.MagicMock(return_value="Test")
    dl_processor.send_sms = mocker.MagicMock()

    dl_processor.send_directory_listing()
    dl_processor.send_sms.assert_called_with(
        'send_directory_listing_message',
        community_token_name="A Token",
        business_type="Test",
        directory_listing_users=f"{user1.phone}\n{user2.phone}"
    )


def test_send_directory_listing_none(mocker, test_client, init_database, dl_processor):
    dl_processor.get_directory_listing_users = mocker.MagicMock(return_value=[])
    dl_processor.get_business_category_translation = mocker.MagicMock(return_value="Test")
    dl_processor.send_sms = mocker.MagicMock()

    dl_processor.send_directory_listing()
    dl_processor.send_sms.assert_called_with('no_directory_listing_found_message')
