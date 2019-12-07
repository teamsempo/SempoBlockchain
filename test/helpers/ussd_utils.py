from server.models.transfer_account import TransferAccount
from server.models.user import User
from server.models.token import Token


def create_transfer_account_for_user(user: User, token: Token, balance: float, is_default: bool = True,
                                     is_ghost: bool = False):
    transfer_account = TransferAccount(bind_to_entity=user)
    transfer_account.token = token
    transfer_account.balance = balance

    if is_default:
        user.default_transfer_account_id = transfer_account.id

    if is_ghost:
        transfer_account.is_ghost = True


def make_kenyan_phone(phone_str):
    phone_list = list(phone_str)
    phone_list[0] = "6"
    phone_list[1] = "1"
    return ''.join(phone_list)
