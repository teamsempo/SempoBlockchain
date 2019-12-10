from typing import List, Callable

from server.models import token


def check_user_liquid_token_type(credit_transfer):
    t = credit_transfer.token
    if t is not None and t.token_type == token.TokenType.LIQUID and not \
            credit_transfer.sender_user.has_group_account_role:
        return True

    return False


def check_group_user_liquid_token_type(credit_transfer):
    t = credit_transfer.token
    if t is not None and t.token_type == token.TokenType.LIQUID and \
            credit_transfer.sender_user.has_group_account_role:
        return True

    return False


def check_user_is_phone_verified_but_no_kyc(credit_transfer):
    if check_user_liquid_token_type(credit_transfer):
        return False

    if credit_transfer.sender_user is not None:
        kyc = credit_transfer.sender_user.kyc_applications
        if len(kyc) > 0:
            if kyc[0].kyc_status == 'VERIFIED':
                return False

        return credit_transfer.sender_user.is_phone_verified

    return False


def check_user_but_no_phone_verified_and_no_kyc(credit_transfer):
    if check_user_liquid_token_type(credit_transfer):
        return False

    if check_user_is_phone_verified_but_no_kyc(credit_transfer):
        return False

    if credit_transfer.sender_user is not None:
        kyc = credit_transfer.sender_user.kyc_applications
        if len(kyc) > 0:
            if kyc[0].kyc_status == 'VERIFIED':
                return False

    return True


def check_user_kyc_verified(credit_transfer):
    if check_user_liquid_token_type(credit_transfer):
        return False

    if credit_transfer.sender_user is not None:
        kyc = credit_transfer.sender_user.kyc_applications

        if len(kyc) == 0:
            return False

        if kyc[0].kyc_status == 'VERIFIED' and kyc[0].type == 'INDIVIDUAL':
            return True

    return False


def check_user_kyc_two_id_verified(credit_transfer):
    if check_user_liquid_token_type(credit_transfer):
        return False

    if credit_transfer.sender_user is not None:
        kyc = credit_transfer.sender_user.kyc_applications

        if len(kyc) == 0:
            return False

        if kyc[0].kyc_status == 'VERIFIED' and kyc[0].type == 'BUSINESS':
            return True

    return False


class TransferLimit(object):

    def __repr__(self):
        return f"<TransferLimit {self.name}>"

    # TODO: change the init to behave nicer. (eg applied to transfer types, application filter can't actually be none)
    def __init__(self, name: str, total_amount: int=None, time_period_days: int=None,
                 transfer_balance_percentage: float=None, transfer_count: int=None,
                 applied_to_transfer_types: List=None, application_filter: Callable=None):

        self.name = name
        self.total_amount = total_amount
        self.time_period_days = time_period_days
        self.transfer_balance_percentage = transfer_balance_percentage
        self.transfer_count = transfer_count
        self.applied_to_transfer_types = applied_to_transfer_types
        self.application_filter = application_filter


LIMITS = [
    TransferLimit('Sempo Level 0', 5000, 7, None, None, ['PAYMENT'], check_user_but_no_phone_verified_and_no_kyc),
    TransferLimit('Sempo Level 0', 10000, 30, None, None, ['PAYMENT'], check_user_but_no_phone_verified_and_no_kyc),
    TransferLimit('Sempo Level 0', 0, 30, None, None, ['WITHDRAWAL', 'DEPOSIT'], check_user_but_no_phone_verified_and_no_kyc),

    TransferLimit('Sempo Level 1', 5000, 7, None, None, ['PAYMENT'], check_user_is_phone_verified_but_no_kyc),
    TransferLimit('Sempo Level 1', 20000, 30, None, None, ['PAYMENT'], check_user_is_phone_verified_but_no_kyc),
    TransferLimit('Sempo Level 1', 0, 30, None, None, ['WITHDRAWAL', 'DEPOSIT'], check_user_is_phone_verified_but_no_kyc),

    TransferLimit('Sempo Level 2', 50000, 7, None, None, ['PAYMENT'], check_user_kyc_verified),
    TransferLimit('Sempo Level 2', 100000, 30, None, None, ['PAYMENT'], check_user_kyc_verified),
    TransferLimit('Sempo Level 2', 50000, 7, None, None, ['WITHDRAWAL', 'DEPOSIT'], check_user_kyc_verified),
    TransferLimit('Sempo Level 2', 100000, 30, None, None, ['WITHDRAWAL', 'DEPOSIT'], check_user_kyc_verified),

    TransferLimit('Sempo Level 3', 500000, 7, None, None, ['PAYMENT'], check_user_kyc_two_id_verified),
    TransferLimit('Sempo Level 3', 1000000, 30, None, None, ['PAYMENT'], check_user_kyc_two_id_verified),
    TransferLimit('Sempo Level 3', 500000, 7, None, None, ['WITHDRAWAL', 'DEPOSIT'], check_user_kyc_two_id_verified),
    TransferLimit('Sempo Level 3', 1000000, 30, None, None, ['WITHDRAWAL', 'DEPOSIT'], check_user_kyc_two_id_verified),

    TransferLimit('GE Liquid Token - Standard User', None, 7, 0.1, 1, ['WITHDRAWAL', 'EXCHANGE'], check_user_liquid_token_type),
    TransferLimit('GE Liquid Token - Group Account User', None, 30, 0.5, 1, ['WITHDRAWAL', 'EXCHANGE'], check_group_user_liquid_token_type)
]
