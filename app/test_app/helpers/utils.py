import os

from server import db
from server.models.token import Token
from server.models.transfer_account import TransferAccount
from server.models.transfer_usage import TransferUsage
from server.models.user import User
from server.utils.ussd.ussd_state_machine import UssdStateMachine


def will_func_test_blockchain():
    return (os.environ.get('DEPLOYMENT_NAME') == 'DOCKER_TEST') or os.environ.get('FORCE_BLOCKCHAIN_TESTS')


def create_transfer_account_for_user(user: User, token: Token, balance: float, is_default: bool = True,
                                     is_ghost: bool = False):
    transfer_account = TransferAccount(bound_entity=user)
    transfer_account.token = token
    transfer_account.set_balance_offset(balance)

    if is_default:
        user.default_transfer_account = transfer_account

    if is_ghost:
        transfer_account.is_ghost = True


def make_kenyan_phone(phone_str):
    phone_list = list(phone_str)
    phone_list[0] = "6"
    phone_list[1] = "1"
    return ''.join(phone_list)


def fake_transfer_mapping(length: int):
    mapping = []
    transfer_usage = TransferUsage.find_or_create("Food")
    db.session.commit()
    for i in range(length):
        mapping.append(UssdStateMachine.make_usage_mapping(transfer_usage))

    return mapping


def assert_resp_status_code(response, status_code):
    try:
        assert response.status_code == status_code
    except AssertionError as e:
        e.args += (f'JSON: {response.json}',)
        raise e
