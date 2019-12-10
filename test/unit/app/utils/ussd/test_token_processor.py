import pytest
from functools import partial
from faker.providers import phone_number
from faker import Faker

from helpers.user import UserFactory
from helpers.ussd_utils import create_transfer_account_for_user
from server.models.token import Token
from server.models.transfer_account import TransferAccount
from server.models.user import User
from server.utils.user import default_transfer_account
from server.utils.ussd.token_processor import TokenProcessor

fake = Faker()
fake.add_provider(phone_number)
phone = partial(fake.msisdn)


def create_transfer_account_for_user(user: User, token: Token, balance: float, is_default: bool = True,
                                     is_ghost: bool = False):
    transfer_account = TransferAccount(bind_to_entity=user)
    transfer_account.token = token
    transfer_account.balance = balance

    if is_default:
        user.default_transfer_account_id = transfer_account.id

    if is_ghost:
        transfer_account.is_ghost = True


@pytest.mark.parametrize("user_type,limit,preferred_language,sample_text", [
    ("standard", 0.1, "en", "per 7"),
    ("standard", 0.1, "sw", "siku 7"),
    ("group", 0.5, "en", "per 30"),
    ("group", 0.5, "sw", "siku 30"),
])
def test_send_balance_sms(mocker, test_client, init_database, initialised_blockchain_network, user_type, limit,
                     preferred_language, sample_text):
    user = UserFactory(preferred_language=preferred_language, phone=phone())
    if user_type == "group":
        user.set_held_role('GROUP_ACCOUNT', 'grassroots_group_account')

    token1 = Token.query.filter_by(symbol="SM1").first()
    token2 = Token.query.filter_by(symbol="SM2").first()
    token3 = Token.query.filter_by(symbol="SM3").first()
    create_transfer_account_for_user(user, token1, 20000)
    create_transfer_account_for_user(user, token2, 35000, is_default=False)
    # this one should not show up in balance
    create_transfer_account_for_user(user, token3, 0, is_default=False, is_ghost=True)

    def mock_convert(exchange_contract, from_token, to_token, from_amount):
        if from_token.symbol == "SM1":
            return from_amount * 1.4
        else:
            return from_amount * 0.8
    mocker.patch('server.bt.get_conversion_amount', mock_convert)


    def mock_send_message(phone, message):
        assert sample_text in message
        assert "SM1 200" in message
        assert "SM2 350" in message
        assert "{:.2f} SM1 (1 SM1 = 1.4 AUD)".format(limit * 200) in message
        assert "{:.2f} SM2 (1 SM2 = 0.8 AUD)".format(limit * 350) in message
        assert "SM3" not in message
    mocker.patch('server.message_processor.send_message', mock_send_message)
    TokenProcessor.send_balance_sms(user)


@pytest.mark.parametrize("user_type,preferred_language,exchange_text,limit_text", [
    ("standard", "en", "For 1 SM1 you get 1.2 KSH", "a maximum of 20.00 SM1 at an agent every 7 days"),
    ("group", "sw", "Kwa kila 1 SM1 utapata 1.2 KSH", "100.00 SM1 kwa wakala baada ya siku 30"),
])
def test_fetch_exchange_rate(mocker, test_client, init_database, initialised_blockchain_network, user_type,
                             preferred_language, exchange_text, limit_text):
    user = UserFactory(preferred_language=preferred_language, phone=phone())
    if user_type == "group":
        user.set_held_role('GROUP_ACCOUNT', 'grassroots_group_account')

    token1 = Token.query.filter_by(symbol="SM1").first()
    create_transfer_account_for_user(user, token1, 20000)

    def mock_convert(exchange_contract, from_token, to_token, from_amount):
            return from_amount * 1.2
    mocker.patch('server.bt.get_conversion_amount', mock_convert)

    def mock_send_message(phone, message):
        assert exchange_text in message
        assert limit_text in message
    mocker.patch('server.message_processor.send_message', mock_send_message)
    TokenProcessor.fetch_exchange_rate(user)


def test_send_token(mocker, test_client, init_database, initialised_blockchain_network):
    sender = UserFactory(preferred_language="en", phone=phone(), first_name="Bob", last_name="Foo")
    token1 = Token.query.filter_by(symbol="SM1").first()
    create_transfer_account_for_user(sender, token1, 20000)

    recipient = UserFactory(phone=phone(), first_name="Joe", last_name="Bar")
    token2 = Token.query.filter_by(symbol="SM2").first()
    create_transfer_account_for_user(recipient, token2, 30000)

    def mock_convert(exchange_contract, from_token, to_token, from_amount, signing_address):
        if from_token.symbol == "SM1":
            return from_amount * 1.5
        else:
            return from_amount * 0.75
    mocker.patch('server.bt.get_conversion_amount', mock_convert)

    messages = []

    def mock_send_message(phone, message):
        messages.append({'phone': phone, 'message': message})
    mocker.patch('server.message_processor.send_message', mock_send_message)

    TokenProcessor.send_token(sender, recipient, 1000, "A reason", 1)
    assert default_transfer_account(sender).balance == 19000
    # TODO: shouldn't it double convert from the reserve to be 32000..?
    assert default_transfer_account(recipient).balance == 31500

    assert len(messages) == 2
    sent_message = messages[0]
    assert sent_message['phone'] == sender.phone
    assert 'sent a payment of 10.00 SM1 = 15.00 SM2' in sent_message['message']
    received_message = messages[1]
    assert received_message['phone'] == recipient.phone
    assert 'received a payment of 15.00 SM2 = 10.00 SM1' in received_message['message']


def test_exchange_token(mocker, test_client, init_database, initialised_blockchain_network):
    sender = UserFactory(preferred_language="en", phone=phone(), first_name="Bob", last_name="Foo")
    token1 = Token.query.filter_by(symbol="SM1").first()
    create_transfer_account_for_user(sender, token1, 20000)

    agent = UserFactory(phone=phone(), first_name="Joe", last_name="Bar")
    agent.set_held_role('TOKEN_AGENT', 'grassroots_token_agent')
    # this is under the assumption that token agent would have default token being the reserve token. is this the case?
    reserve = Token.query.filter_by(symbol="AUD").first()
    create_transfer_account_for_user(agent, reserve, 30000)

    def mock_convert(exchange_contract, from_token, to_token, from_amount, signing_address):
        return from_amount * 1.2
    mocker.patch('server.bt.get_conversion_amount', mock_convert)

    messages = []

    def mock_send_message(phone, message):
        messages.append({'phone': phone, 'message': message})
    mocker.patch('server.message_processor.send_message', mock_send_message)

    TokenProcessor.exchange_token(sender, agent, 1000)
    assert default_transfer_account(sender).balance == 19000
    assert default_transfer_account(agent).balance == 31200

    assert len(messages) == 2
    sent_message = messages[0]
    assert sent_message['phone'] == sender.phone
    assert 'sent a payment of 10.00 SM1 = 12.00 AUD' in sent_message['message']
    received_message = messages[1]
    assert received_message['phone'] == agent.phone
    assert 'received a payment of 12.00 AUD = 10.00 SM1' in received_message['message']

