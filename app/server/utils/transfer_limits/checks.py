from server.models import token
from server.models.credit_transfer import CreditTransfer
from server.utils.access_control import AccessControl
from server.utils.transfer_enums import TransferSubTypeEnum


# ~~~~~~SIMPLE CHECKS~~~~~~
def sempo_admin_involved(credit_transfer):
    if credit_transfer.recipient_user and AccessControl.has_sufficient_tier(
            credit_transfer.recipient_user.roles, 'ADMIN', 'sempoadmin'):
        return True

    if credit_transfer.sender_user and AccessControl.has_sufficient_tier(
            credit_transfer.sender_user.roles, 'ADMIN', 'sempoadmin'):
        return True

    return False


def sender_user_exists(credit_transfer: CreditTransfer):
    return credit_transfer.sender_user


def user_has_group_account_role(credit_transfer):
    return credit_transfer.sender_user.has_group_account_role


def user_phone_is_verified(credit_transfer):
    return credit_transfer.sender_user.is_phone_verified


def user_individual_kyc_is_verified(credit_transfer):
    return _sender_matches_kyc_criteria(
        credit_transfer,
        lambda app: app.kyc_status == 'VERIFIED' and app.type == 'INDIVIDUAL' and not app.multiple_documents_verified
    )


def user_business_or_multidoc_kyc_verified(credit_transfer):
    return _sender_matches_kyc_criteria(
        credit_transfer,
        lambda app: app.kyc_status == 'VERIFIED'
                    and (app.type == 'BUSINESS' or app.multiple_documents_verified)
    )


def _sender_matches_kyc_criteria(credit_transfer, criteria):
    if credit_transfer.sender_user is not None:
        matches_criteria = next((app for app in credit_transfer.sender_user.kyc_applications if criteria(app)), None)
        return bool(matches_criteria)
    return False


def token_is_liquid_type(credit_transfer):
    return credit_transfer.token and credit_transfer.token.token_type is token.TokenType.LIQUID


def token_is_reserve_type(credit_transfer):
    return credit_transfer.token and credit_transfer.token.token_type is token.TokenType.RESERVE


def transfer_is_agent_out_subtype(credit_transfer):
    return credit_transfer.transfer_subtype is TransferSubTypeEnum.AGENT_OUT


# ~~~~~~COMPOSITE CHECKS~~~~~~
def base_check(credit_transfer):
    # Only ever check transfers with a sender user and no sempoadmin (those involving sempoadmins are always allowed)
    return sender_user_exists(credit_transfer) and not sempo_admin_involved(credit_transfer)


def is_user_and_any_token(credit_transfer):
    return base_check(credit_transfer) \
           and (token_is_reserve_type(credit_transfer) or token_is_liquid_type(credit_transfer))


def is_user_and_liquid_token(credit_transfer):
    return base_check(credit_transfer) and token_is_liquid_type(credit_transfer) \
           and not user_has_group_account_role(credit_transfer)


def is_group_and_liquid_token(credit_transfer):
    return base_check(credit_transfer) and token_is_liquid_type(credit_transfer) \
           and user_has_group_account_role(credit_transfer)


def is_any_token_and_user_is_not_phone_and_not_kyc_verified(credit_transfer):
    return is_user_and_any_token(credit_transfer) and \
           not user_phone_is_verified(credit_transfer) and not user_individual_kyc_is_verified(credit_transfer)


def is_any_token_and_user_is_phone_but_not_kyc_verified(credit_transfer):
    return is_user_and_any_token(credit_transfer) and user_phone_is_verified(credit_transfer) and not (
            user_individual_kyc_is_verified(credit_transfer) or user_business_or_multidoc_kyc_verified(credit_transfer)
    )


def is_any_token_and_user_is_kyc_verified(credit_transfer):
    return is_user_and_any_token(credit_transfer) and user_individual_kyc_is_verified(credit_transfer)


def is_any_token_and_user_is_kyc_business_verified(credit_transfer):
    return is_user_and_any_token(credit_transfer) and user_business_or_multidoc_kyc_verified(credit_transfer)