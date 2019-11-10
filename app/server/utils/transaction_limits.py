from server.models import user, token, credit_transfer


def user_is_phone_verified_but_no_kyc(object, credit_transfer):
    if not isinstance(object, user.User):
        return False

    kyc = object.kyc_applications
    if len(kyc) > 0:
        if kyc[0].kyc_status == 'VERIFIED':
            return False

    if not object.is_self_sign_up:
        return True

    return object.is_phone_verified


def check_user_kyc_and_phone(object, credit_transfer):
    if not isinstance(object, user.User):
        return False

    if len(object.kyc_applications) == 0 and not user_is_phone_verified_but_no_kyc(object, None):
        return True

    return False


def check_user_kyc_verified(object, credit_transfer):
    if not isinstance(object, user.User):
        return False

    kyc = object.kyc_applications
    if len(kyc) == 0:
        return False

    if kyc[0].kyc_status == 'VERIFIED' and kyc[0].type == 'INDIVIDUAL':
        return True

    return False


def check_user_kyc_two_id_verified(object, credit_transfer):
    if not isinstance(object, user.User):
        return False

    kyc = object.kyc_applications
    if len(kyc) == 0:
        return False

    if kyc[0].kyc_status == 'VERIFIED' and kyc[0].type == 'BUSINESS':
        return True

    return False


def check_user_liquid_token_type(object, credit_transfer):
    if not isinstance(credit_transfer, credit_transfer.CreditTransfer):
        return False

    t = token.Token.query.get(credit_transfer.token_id)
    if t is not None and t.token_type == token.TokenType.LIQUID:
        return True

    return False


def check_group_user_liquid_token_type(object, credit_transfer):
    if not isinstance(object, user.User):
        return False
    if not isinstance(credit_transfer, credit_transfer.CreditTransfer):
        return False

    t = token.Token.query.get(credit_transfer.token_id)
    if t is not None and t.token_type == token.TokenType.LIQUID:
        # TODO: add group account check
        return True
    return False


limits = [
    {
        'rule': {'name': 'Sempo Level 0', 'total_amount': 5000, 'time_period_days': 7, 'txn_type': 'PAYMENT'},
        'applied_when': check_user_kyc_and_phone,
    },
    {
        'rule': {'name': 'Sempo Level 0', 'total_amount': 10000, 'time_period_days': 30, 'txn_type': 'PAYMENT'},
        'applied_when': check_user_kyc_and_phone,
    },
    {
        'rule': {'name': 'Sempo Level 0', 'total_amount': 0, 'time_period_days': 30, 'txn_type': ['WITHDRAWAL', 'DEPOSIT']},
        'applied_when': check_user_kyc_and_phone,
    },
    {
        'rule': {'name': 'Sempo Level 1', 'total_amount': 5000, 'time_period_days': 7, 'txn_type': 'PAYMENT'},
        'applied_when': user_is_phone_verified_but_no_kyc,
    },
    {
        'rule': {'name': 'Sempo Level 1', 'total_amount': 20000, 'time_period_days': 30, 'txn_type': 'PAYMENT'},
        'applied_when': user_is_phone_verified_but_no_kyc,
    },
    {
        'rule': {'name': 'Sempo Level 1', 'total_amount': 0, 'time_period_days': 30, 'txn_type': ['WITHDRAWAL', 'DEPOSIT']},
        'applied_when': user_is_phone_verified_but_no_kyc,
    },
    {
        'rule': {'name': 'Sempo Level 2', 'total_amount': 50000, 'time_period_days': 7, 'txn_type': 'PAYMENT'},
        'applied_when': check_user_kyc_verified,
    },
    {
        'rule': {'name': 'Sempo Level 2', 'total_amount': 100000, 'time_period_days': 30, 'txn_type': 'PAYMENT'},
        'applied_when': check_user_kyc_verified,
    },
    {
        'rule': {'name': 'Sempo Level 2', 'total_amount': 50000, 'time_period_days': 7, 'txn_type': ['WITHDRAWAL', 'DEPOSIT']},
        'applied_when': check_user_kyc_verified,
    },
    {
        'rule': {'name': 'Sempo Level 2', 'total_amount': 100000, 'time_period_days': 30, 'txn_type': ['WITHDRAWAL', 'DEPOSIT']},
        'applied_when': check_user_kyc_verified,
    },
    {
        'rule': {'name': 'Sempo Level 3', 'total_amount': 500000, 'time_period_days': 7, 'txn_type': 'PAYMENT'},
        'applied_when': check_user_kyc_two_id_verified,
    },
    {
        'rule': {'name': 'Sempo Level 3', 'total_amount': 1000000, 'time_period_days': 30, 'txn_type': 'PAYMENT'},
        'applied_when': check_user_kyc_two_id_verified,
    },
    {
        'rule': {'name': 'Sempo Level 3', 'total_amount': 500000, 'time_period_days': 7, 'txn_type': ['WITHDRAWAL', 'DEPOSIT']},
        'applied_when': check_user_kyc_two_id_verified,
    },
    {
        'rule': {'name': 'Sempo Level 3', 'total_amount': 1000000, 'time_period_days': 30, 'txn_type': ['WITHDRAWAL', 'DEPOSIT']},
        'applied_when': check_user_kyc_two_id_verified,
    },
    {
        'rule': {'name': 'GE Liquid Token - Standard User', 'total_amount': None, 'txn_balance_percentage': 0.1, 'txn_count': 1, 'time_period_days': 7, 'txn_type': 'WITHDRAWAL'},
        'applied_when': check_user_liquid_token_type,
    },
    # {
    #     'rule': {'name': 'GE Liquid Token - Group User', 'total_amount': None, 'txn_balance_percentage': 0.5, 'txn_count': 1, 'time_period_days': 30, 'txn_type': 'WITHDRAWAL'},
    #     'applied_when': check_group_user_liquid_token_type,
    # }
]
