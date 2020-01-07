import pytest
from functools import partial
from faker.providers import phone_number
from faker import Faker

from helpers.factories import UserFactory
from helpers.ussd_utils import create_transfer_account_for_user
from server.models.token import Token
from server.models.transfer_usage import TransferUsage
from server.utils.credit_transfer import make_payment_transfer
from server.utils.user import default_transfer_account, set_custom_attributes
from server.utils.ussd.directory_listing_processor import DirectoryListingProcessor

fake = Faker()
fake.add_provider(phone_number)
phone = partial(fake.msisdn)


@pytest.fixture(scope='function')
def dl_processor(initialised_blockchain_network, create_transfer_usage):
    transfer_usage = create_transfer_usage

    user = UserFactory(phone=phone(), business_usage_id=transfer_usage.id)
    token = Token.query.filter_by(symbol="SM1").first()
    create_transfer_account_for_user(user, token, 200)
    return DirectoryListingProcessor(user, transfer_usage)


def test_get_directory_listing_users(test_client, init_database, dl_processor):
    token1 = Token.query.filter_by(symbol="SM1").first()
    category = dl_processor.selected_business_category
    user = dl_processor.recipient

    def create_user(cat, token):
        user = UserFactory(phone=phone(), business_usage_id=cat.id)
        create_transfer_account_for_user(user, token, 200)
        return user

    market_disabled_user = create_user(category, token1)
    attrs = {
        "custom_attributes": {
            "market_enabled": False
        }
    }
    set_custom_attributes(attrs, market_disabled_user)

    # different category user
    token2 = Token.query.filter_by(symbol="SM2").first()
    create_user(category, token2)

    category2 = TransferUsage(name='Test', icon='message')
    different_business_category_user = create_user(category2, token1)

    shown_user = create_user(category, token1)
    # user did more transactions
    more_transactions_user = create_user(category, token1)
    make_payment_transfer(100, token=token1, send_user=different_business_category_user,
                          receive_user=more_transactions_user,
                          transfer_use=str(int(category.id)), is_ghost_transfer=False,
                          require_sender_approved=False, require_recipient_approved=False)
    make_payment_transfer(100, token=token1, send_user=different_business_category_user,
                          receive_user=more_transactions_user,
                          transfer_use=str(int(category.id)), is_ghost_transfer=False,
                          require_sender_approved=False, require_recipient_approved=False)

    users = dl_processor.get_directory_listing_users()
    assert len(users) == 2
    assert users[0].id == more_transactions_user.id
    assert users[1].id == shown_user.id


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
    transfer_account = default_transfer_account(user)
    transfer_account.token.name = "A Token"

    user1 = UserFactory(phone=phone())
    attrs = {
        "custom_attributes": {
            "bio": "some bio"
        }
    }
    set_custom_attributes(attrs, user1)
    user2 = UserFactory(phone=phone())
    dl_processor.get_directory_listing_users = mocker.MagicMock(return_value=[user1, user2])
    dl_processor.get_business_category_translation = mocker.MagicMock(return_value="Test")
    dl_processor.send_sms = mocker.MagicMock()

    dl_processor.send_directory_listing()
    dl_processor.send_sms.assert_called_with(
        'send_directory_listing_message',
        community_token_name="A Token",
        business_type="Test",
        directory_listing_users=f"{user1.phone} some bio\n{user2.phone}"
    )


def test_send_directory_listing_none(mocker, test_client, init_database, dl_processor):
    dl_processor.get_directory_listing_users = mocker.MagicMock(return_value=[])
    dl_processor.get_business_category_translation = mocker.MagicMock(return_value="Test")
    dl_processor.send_sms = mocker.MagicMock()

    dl_processor.send_directory_listing()
    dl_processor.send_sms.assert_called_with('no_directory_listing_found_message')
