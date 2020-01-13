from typing import List, Callable, Optional, Union, Tuple
import datetime
from toolz import curry, pipe
from sqlalchemy import or_
from sqlalchemy.orm import Query

from server.exceptions import TransferLimitCreationError

from server.models import token
from server.models.credit_transfer import CreditTransfer
from server.utils.transfer_enums import TransferSubTypeEnum, TransferTypeEnum, TransferStatusEnum
import config

AppliedToTypes = List[Union[TransferTypeEnum,
                            Tuple[TransferTypeEnum, TransferSubTypeEnum]]]

PAYMENT = TransferTypeEnum.PAYMENT
DEPOSIT = TransferTypeEnum.DEPOSIT
WITHDRAWAL = TransferTypeEnum.WITHDRAWAL

AGENT_OUT = TransferSubTypeEnum.AGENT_OUT
AGENT_IN = TransferSubTypeEnum.AGENT_IN
STANDARD = TransferSubTypeEnum.STANDARD

STANDARD_PAYMENT = (PAYMENT, STANDARD)
AGENT_OUT_PAYMENT = (PAYMENT, AGENT_OUT)
AGENT_IN_PAYMENT = (PAYMENT, AGENT_IN)


def get_transfer_limits(credit_transfer: CreditTransfer):
    relevant_limits = []
    for limit in LIMITS:
        applied = limit.application_filter(credit_transfer)
        if applied and (credit_transfer.transfer_type in limit.applied_to_transfer_types
                        or (credit_transfer.transfer_type, credit_transfer.transfer_subtype)
                        in limit.applied_to_transfer_types):
            
            relevant_limits.append(limit)

    return relevant_limits


    # # Supports filtering over type-subtype tuples of the form ('PAYMENT', 'AGENT_OUT')
    # applied = limit.application_filter(self)
    # if applied:
    #     for transfer_type in limit.applied_to_transfer_types:
    #         if isinstance(transfer_type, (tuple, list)):
    #             if str(self.transfer_type) == transfer_type[0]\
    #                     and str(self.transfer_subtype) == transfer_type[1]:
    #                 relevant_limits.append(limit)
    #                 continue
    #         else:
    #             if str(self.transfer_type) == transfer_type:
    #                 relevant_limits.append(limit)
    #                 continue

# ~~~~~~SIMPLE CHECKS~~~~~~

def sender_user_exists(credit_transfer):
    return credit_transfer.sender_user


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


def token_is_reserve_type(credit_transfer):
    return credit_transfer.token and credit_transfer.token.token_type is token.TokenType.RESERVE


def transfer_is_agent_out_subtype(credit_transfer):
    return credit_transfer.transfer_subtype is TransferSubTypeEnum.AGENT_OUT

# ~~~~~~COMPOSITE CHECKS~~~~~~


def is_user_and_any_token(credit_transfer):
    return sender_user_exists(credit_transfer) \
           and (token_is_reserve_type(credit_transfer) or token_is_liquid_type(credit_transfer))


def is_user_and_liquid_token(credit_transfer):
    return sender_user_exists(credit_transfer) and token_is_liquid_type(credit_transfer) \
           and not user_has_group_account_role(credit_transfer)


def is_group_and_liquid_token(credit_transfer):
    return sender_user_exists(credit_transfer) and token_is_liquid_type(credit_transfer) \
           and user_has_group_account_role(credit_transfer)


def is_any_token_and_user_is_not_phone_and_not_kyc_verified(credit_transfer):
    return is_user_and_any_token(credit_transfer) and \
           not user_phone_is_verified(credit_transfer) and not user_individual_kyc_is_verified(credit_transfer)


def is_any_token_and_user_is_phone_but_not_kyc_verified(credit_transfer):
    return is_user_and_any_token(credit_transfer) and user_phone_is_verified(credit_transfer) and not (
        user_individual_kyc_is_verified(credit_transfer) or user_business_kyc_is_verified(credit_transfer)
    )


def is_any_token_and_user_is_kyc_verified(credit_transfer):
    return is_user_and_any_token(credit_transfer) and user_individual_kyc_is_verified(credit_transfer)


def is_any_token_and_user_is_kyc_business_verified(credit_transfer):
    return is_user_and_any_token(credit_transfer) and user_business_kyc_is_verified(credit_transfer)

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
def withdrawal_or_agent_out_filter(transfer: CreditTransfer, query: Query):
    return query.filter(or_(CreditTransfer.transfer_type == TransferTypeEnum.WITHDRAWAL,
                            CreditTransfer.transfer_subtype == TransferSubTypeEnum.AGENT_OUT))


@curry
def not_rejected_filter(query: Query):
    return query.filter(CreditTransfer.transfer_status != TransferStatusEnum.REJECTED)


@curry
def empty_filter(transfer: CreditTransfer, query: Query):
    return query


class TransferLimit(object):

    def __repr__(self):
        return f"<TransferLimit {self.name}>"

    def apply_all_filters(self, transfer: CreditTransfer, query: Query):

        return pipe(query,
                    matching_sender_user_filter(transfer),
                    not_rejected_filter,
                    after_time_period_filter(self.time_period_days),
                    self.transfer_filter(transfer))

    def __init__(self,
                 name: str,
                 applied_to_transfer_types: AppliedToTypes,
                 application_filter: Callable,
                 time_period_days: int,
                 total_amount: Optional[int] = None,
                 transfer_count: Optional[int] = None,
                 transfer_filter: Optional[Query.filter] = matching_transfer_type_filter,
                 transfer_balance_fraction: Optional[float] = None):

        self.name = name

        # Force to list of tuples to ensure the use of 'in' behaves as expected
        self.applied_to_transfer_types = [tuple(t) if isinstance(t, list) else t for t in applied_to_transfer_types]

        self.application_filter = application_filter
        self.time_period_days = time_period_days
        # TODO: Make LIMIT_EXCHANGE_RATE configurable per org
        self.total_amount = int(total_amount * config.LIMIT_EXCHANGE_RATE) if total_amount else None
        self.transfer_count = transfer_count
        self.transfer_filter = transfer_filter
        self.transfer_balance_fraction = transfer_balance_fraction

        if transfer_balance_fraction and total_amount:
            raise TransferLimitCreationError('Cannot have transfer_balance_fraction and total_amount')


LIMITS = [
    TransferLimit('Sempo Level 0: P7', [STANDARD_PAYMENT, AGENT_OUT_PAYMENT, AGENT_IN_PAYMENT],
                  is_any_token_and_user_is_not_phone_and_not_kyc_verified, 7,
                  total_amount=5000),
    TransferLimit('Sempo Level 0: P30', [STANDARD_PAYMENT, AGENT_OUT_PAYMENT, AGENT_IN_PAYMENT],
                  is_any_token_and_user_is_not_phone_and_not_kyc_verified, 30,
                  total_amount=10000),

    TransferLimit('Sempo Level 0: WD30', [WITHDRAWAL, DEPOSIT],
                  is_any_token_and_user_is_not_phone_and_not_kyc_verified, 30,
                  total_amount=0),

    TransferLimit('Sempo Level 1: P7', [STANDARD_PAYMENT, AGENT_OUT_PAYMENT, AGENT_IN_PAYMENT],
                  is_any_token_and_user_is_phone_but_not_kyc_verified, 7,
                  total_amount=5000),
    TransferLimit('Sempo Level 1: P30', [STANDARD_PAYMENT, AGENT_OUT_PAYMENT, AGENT_IN_PAYMENT],
                  is_any_token_and_user_is_phone_but_not_kyc_verified, 30,
                  total_amount=20000),
    TransferLimit('Sempo Level 1: WD30', [WITHDRAWAL, DEPOSIT],
                  is_any_token_and_user_is_phone_but_not_kyc_verified, 30,
                  total_amount=0),

    TransferLimit('Sempo Level 2: P7', [STANDARD_PAYMENT, AGENT_OUT_PAYMENT, AGENT_IN_PAYMENT],
                  is_any_token_and_user_is_kyc_verified, 7,
                  total_amount=50000),
    TransferLimit('Sempo Level 2: P30', [STANDARD_PAYMENT, AGENT_OUT_PAYMENT, AGENT_IN_PAYMENT],
                  is_any_token_and_user_is_kyc_verified, 30,
                  total_amount=100000),
    TransferLimit('Sempo Level 2: WD7', [WITHDRAWAL, DEPOSIT], is_any_token_and_user_is_kyc_verified, 7,
                  total_amount=50000),
    TransferLimit('Sempo Level 2: WD30', [WITHDRAWAL, DEPOSIT], is_any_token_and_user_is_kyc_verified, 30,
                  total_amount=100000),

    TransferLimit('Sempo Level 3: P7', [STANDARD_PAYMENT, AGENT_OUT_PAYMENT, AGENT_IN_PAYMENT],
                  is_any_token_and_user_is_kyc_business_verified, 7,
                  total_amount=500000),
    TransferLimit('Sempo Level 3: P30', [STANDARD_PAYMENT, AGENT_OUT_PAYMENT, AGENT_IN_PAYMENT],
                  is_any_token_and_user_is_kyc_business_verified, 30,
                  total_amount=1000000),
    TransferLimit('Sempo Level 3: WD7', [WITHDRAWAL, DEPOSIT],
                  is_any_token_and_user_is_kyc_business_verified, 7,
                  total_amount=500000),
    TransferLimit('Sempo Level 3: WD30', [WITHDRAWAL, DEPOSIT],
                  is_any_token_and_user_is_kyc_business_verified, 30,
                  total_amount=1000000),


    TransferLimit('GE Liquid Token - Standard User',
                  [AGENT_OUT_PAYMENT, WITHDRAWAL], is_user_and_liquid_token, 7,
                  transfer_filter=withdrawal_or_agent_out_filter,
                  # transfer_count=1, transfer_balance_fraction=0.10),
                  ),

    TransferLimit('GE Liquid Token - Group Account User',
                  [AGENT_OUT_PAYMENT, WITHDRAWAL], is_group_and_liquid_token, 30,
                  transfer_filter=withdrawal_or_agent_out_filter,
                  transfer_count=1, transfer_balance_fraction=0.50)
]

