from typing import List, Callable, Optional
import datetime
from toolz import curry, pipe
from sqlalchemy.orm import Query

from server.models import token
from server.models.credit_transfer import CreditTransfer
from server.utils.transfer_enums import TransferSubTypeEnum, TransferTypeEnum

PAYMENT = TransferTypeEnum.PAYMENT
DEPOSIT = TransferTypeEnum.DEPOSIT
WITHDRAWAL = TransferTypeEnum.WITHDRAWAL

# ~~~~~~SIMPLE CHECKS~~~~~~


def user_has_group_account_role(credit_transfer):
    return credit_transfer.sender_user.has_group_account_role


def user_phone_is_verified(credit_transfer):
    return credit_transfer.sender_user.is_phone_verified


def user_individual_kyc_is_verified(credit_transfer):
    if credit_transfer.sender_user is not None:
        kyc = credit_transfer.sender_user.kyc_applications
        if len(kyc) > 0 and kyc[0].kyc_status == 'VERIFIED' and kyc[0].type == 'INDIVIDUAL':
            return True

    return False


def user_business_kyc_is_verified(credit_transfer):
    if credit_transfer.sender_user is not None:
        kyc = credit_transfer.sender_user.kyc_applications
        if len(kyc) > 0 and kyc[0].kyc_status == 'VERIFIED' and kyc[0].type == 'BUSINESS':
            return True

    return False


def token_is_liquid_type(credit_transfer):
    return credit_transfer.token and credit_transfer.token.token_type is token.TokenType.LIQUID


def transfer_is_agent_out_subtype(credit_transfer):
    return credit_transfer.transfer_subtype is TransferSubTypeEnum.AGENT_OUT

# ~~~~~~COMPOSITE CHECKS~~~~~~


def is_user_and_liquid_token(credit_transfer):
    return token_is_liquid_type(credit_transfer) and not user_has_group_account_role(credit_transfer)


def is_group_and_liquid_token(credit_transfer):
    return token_is_liquid_type(credit_transfer) and user_has_group_account_role(credit_transfer)


def is_liquid_and_user_is_not_phone_and_not_kyc_verified(credit_transfer):
    if is_user_and_liquid_token(credit_transfer):
        return False

    return not user_phone_is_verified(credit_transfer) and not user_individual_kyc_is_verified(credit_transfer)


def is_liquid_and_user_is_phone_but_not_kyc_verified(credit_transfer):
    if is_user_and_liquid_token(credit_transfer):
        return False

    return user_phone_is_verified(credit_transfer) and not (
        user_individual_kyc_is_verified(credit_transfer) or user_business_kyc_is_verified(credit_transfer)
    )


def is_liquid_and_user_is_kyc_verified(credit_transfer):
    if is_user_and_liquid_token(credit_transfer):
        return False

    return user_individual_kyc_is_verified(credit_transfer)


def is_liquid_and_user_is_kyc_business_verified(credit_transfer):
    if is_user_and_liquid_token(credit_transfer):
        return False

    return user_business_kyc_is_verified(credit_transfer)

# ~~~~~~LIMIT FILTERS~~~~~~


@curry
def after_time_period_filter(days: int, query: Query):

    epoch = datetime.datetime.today() - datetime.timedelta(days=days)

    return query.filter(CreditTransfer.created >= epoch)


@curry
def matching_sender_user_filter(transfer: CreditTransfer, query: Query):
    return query.filter(CreditTransfer.sender_user == transfer.sender_user)


@curry
def matching_transfer_type_filter(transfer: CreditTransfer, query: Query,):
    return query.filter(CreditTransfer.transfer_type == transfer.transfer_type)


@curry
def matching_transfer_type_and_subtype_filter(transfer: CreditTransfer, query: Query):
    return (query
            .filter(CreditTransfer.transfer_type == transfer.transfer_type)
            .filter(CreditTransfer.transfer_subtype == transfer.transfer_subtype))


@curry
def empty_filter(query: Query, transfer: CreditTransfer):
    return query


class TransferLimit(object):

    def __repr__(self):
        return f"<TransferLimit {self.name}>"

    def apply_all_filters(self, transfer: CreditTransfer, query: Query):

        return pipe(query,
                    matching_sender_user_filter(transfer),
                    after_time_period_filter(self.time_period_days),
                    self.transfer_filter(transfer))

    def __init__(self,
                 name: str,
                 applied_to_transfer_types: List,
                 application_filter: Callable,
                 time_period_days: int,
                 total_amount: Optional[int] = None,
                 transfer_count: Optional[int] = None,
                 transfer_filter: Optional[Query.filter] = matching_transfer_type_filter,
                 transfer_balance_fraction: Optional[float] = None):

        self.name = name
        self.applied_to_transfer_types = applied_to_transfer_types
        self.application_filter = application_filter
        self.time_period_days = time_period_days
        self.total_amount = total_amount
        self.transfer_count = transfer_count
        self.transfer_filter = transfer_filter
        self.transfer_balance_fraction = transfer_balance_fraction


LIMITS = [
    TransferLimit('Sempo Level 0', [PAYMENT], is_liquid_and_user_is_not_phone_and_not_kyc_verified, 7,
                  total_amount=5000),
    TransferLimit('Sempo Level 0', [PAYMENT], is_liquid_and_user_is_not_phone_and_not_kyc_verified, 30,
                  total_amount=10000),
    TransferLimit('Sempo Level 0', [WITHDRAWAL, DEPOSIT], is_liquid_and_user_is_not_phone_and_not_kyc_verified, 30,
                  total_amount=0),

    TransferLimit('Sempo Level 1', [PAYMENT], is_liquid_and_user_is_phone_but_not_kyc_verified, 7,
                  total_amount=5000),
    TransferLimit('Sempo Level 1', [PAYMENT], is_liquid_and_user_is_phone_but_not_kyc_verified, 30,
                  total_amount=20000),
    TransferLimit('Sempo Level 1', [WITHDRAWAL, DEPOSIT], is_liquid_and_user_is_phone_but_not_kyc_verified, 30,
                  total_amount=0),

    TransferLimit('Sempo Level 2', [PAYMENT], is_liquid_and_user_is_kyc_verified, 7,
                  total_amount=50000),
    TransferLimit('Sempo Level 2', [PAYMENT], is_liquid_and_user_is_kyc_verified, 30,
                  total_amount=100000),
    TransferLimit('Sempo Level 2', [WITHDRAWAL, DEPOSIT], is_liquid_and_user_is_kyc_verified, 7,
                  total_amount=50000),
    TransferLimit('Sempo Level 2', [WITHDRAWAL, DEPOSIT], is_liquid_and_user_is_kyc_verified, 30,
                  total_amount=100000),

    TransferLimit('Sempo Level 3', [PAYMENT], is_liquid_and_user_is_kyc_business_verified, 7,
                  total_amount=500000),
    TransferLimit('Sempo Level 3', [PAYMENT], is_liquid_and_user_is_kyc_business_verified, 30,
                  total_amount=1000000),
    TransferLimit('Sempo Level 3', [WITHDRAWAL, DEPOSIT], is_liquid_and_user_is_kyc_business_verified, 7,
                  total_amount=500000),
    TransferLimit('Sempo Level 3', [WITHDRAWAL, DEPOSIT], is_liquid_and_user_is_kyc_business_verified, 30,
                  total_amount=1000000),

    TransferLimit('GE Liquid Token - Standard User', [PAYMENT],
                  lambda c: is_user_and_liquid_token(c) and transfer_is_agent_out_subtype(c), 7,
                  transfer_count=1, transfer_filter=matching_transfer_type_and_subtype_filter,
                  transfer_balance_fraction=0.10),

    TransferLimit('GE Liquid Token - Standard User', [WITHDRAWAL],
                  is_user_and_liquid_token, 7, transfer_count=1, transfer_balance_fraction=0.10),

    TransferLimit('GE Liquid Token - Group Account User', [PAYMENT],
                  lambda c: is_group_and_liquid_token(c) and transfer_is_agent_out_subtype(c), 30,
                  transfer_count=1, transfer_filter=matching_transfer_type_and_subtype_filter,
                  transfer_balance_fraction=0.50),

    TransferLimit('GE Liquid Token - Group Account User', [WITHDRAWAL],
                  is_group_and_liquid_token, 30, transfer_count=1, transfer_balance_fraction=0.50)
]

