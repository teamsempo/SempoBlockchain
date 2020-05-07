from typing import List, Callable, Optional, Union, Tuple, Iterable
from abc import ABC, abstractmethod

import datetime
from functools import reduce
from toolz import curry, pipe
from sqlalchemy import or_
from sqlalchemy.orm import Query
from sqlalchemy.sql import func

from server.exceptions import (
    NoTransferAllowedLimitError,
    MinimumSentLimitError,
    TransferAmountLimitError,
    TransferCountLimitError,
    TransferBalanceFractionLimitError)

from server.models import token
from server import db
from server.sempo_types import TransferAmount
from server.models.credit_transfer import CreditTransfer
from server.utils.transfer_enums import TransferSubTypeEnum, TransferTypeEnum, TransferStatusEnum
from server.utils.access_control import AccessControl
import config

AppliedToTypes = List[Union[TransferTypeEnum,
                            Tuple[TransferTypeEnum, TransferSubTypeEnum]]]

PAYMENT = TransferTypeEnum.PAYMENT
DEPOSIT = TransferTypeEnum.DEPOSIT
WITHDRAWAL = TransferTypeEnum.WITHDRAWAL

AGENT_OUT = TransferSubTypeEnum.AGENT_OUT
AGENT_IN = TransferSubTypeEnum.AGENT_IN
STANDARD = TransferSubTypeEnum.STANDARD
RECLAMATION = TransferSubTypeEnum.RECLAMATION

STANDARD_PAYMENT = (PAYMENT, STANDARD)
AGENT_OUT_PAYMENT = (PAYMENT, AGENT_OUT)
AGENT_IN_PAYMENT = (PAYMENT, AGENT_IN)
RECLAMATION_PAYMENT = (PAYMENT, RECLAMATION)

GENERAL_PAYMENTS = [STANDARD_PAYMENT, AGENT_OUT_PAYMENT, AGENT_IN_PAYMENT, RECLAMATION_PAYMENT]


def get_transfer_limits(credit_transfer: CreditTransfer):
    relevant_limits = []
    for limit in LIMITS:
        applied = limit.application_filter(credit_transfer)
        if applied and (credit_transfer.transfer_type in limit.applied_to_transfer_types
                        or (credit_transfer.transfer_type, credit_transfer.transfer_subtype)
                        in limit.applied_to_transfer_types):
            relevant_limits.append(limit)

    return relevant_limits


# ~~~~~~SIMPLE CHECKS~~~~~~

def sempo_admin_involved(credit_transfer):
    if credit_transfer.recipient_user and AccessControl.has_sufficient_tier(
            credit_transfer.recipient_user.roles, 'ADMIN', 'sempoadmin'):
        return True

    if credit_transfer.sender_user and AccessControl.has_sufficient_tier(
            credit_transfer.sender_user.roles, 'ADMIN', 'sempoadmin'):
        return True

    return False


def sender_user_exists(credit_transfer):
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


# ~~~~~~LIMIT FILTERS~~~~~~


@curry
def after_time_period_filter(days: int, query: Query):
    epoch = datetime.datetime.today() - datetime.timedelta(days=days)

    return query.filter(CreditTransfer.created >= epoch)


@curry
def matching_sender_user_filter(transfer: CreditTransfer, query: Query):
    return query.filter(CreditTransfer.sender_user == transfer.sender_user)


@curry
def regular_payment_filter(query: Query):
    return query.filter(CreditTransfer.transfer_subtype == TransferSubTypeEnum.STANDARD)


@curry
def matching_transfer_type_filter(transfer: CreditTransfer, query: Query, ):
    return query.filter(CreditTransfer.transfer_type == transfer.transfer_type)


@curry
def matching_transfer_type_and_subtype_filter(transfer: CreditTransfer, query: Query):
    return (query
            .filter(CreditTransfer.transfer_type == transfer.transfer_type)
            .filter(CreditTransfer.transfer_subtype == transfer.transfer_subtype))


@curry
def withdrawal_or_agent_out_and_not_excluded_filter(transfer: CreditTransfer, query: Query):
    return (query
            .filter(or_(CreditTransfer.transfer_type == TransferTypeEnum.WITHDRAWAL,
                        CreditTransfer.transfer_subtype == TransferSubTypeEnum.AGENT_OUT))
            .filter(CreditTransfer.exclude_from_limit_calcs == False)
            )


@curry
def not_rejected_filter(query: Query):
    return query.filter(CreditTransfer.transfer_status != TransferStatusEnum.REJECTED)


@curry
def empty_filter(transfer: CreditTransfer, query: Query):
    return query


class TransferLimit(ABC):

    @abstractmethod
    def validate_transfer(self, transfer: CreditTransfer):
        pass

    @abstractmethod
    def get_allowance(self, transfer: CreditTransfer) -> Union[int, TransferAmount]:
        pass

    def _aggregate_transfers(self, transfer: CreditTransfer):
        # Not specified as an abstract method because a few classes don't use it
        pass

    def _aggregate_transfer_query(self, transfer: CreditTransfer, query: Query):
        return pipe(query,
                    matching_sender_user_filter(transfer),
                    not_rejected_filter,
                    after_time_period_filter(self.time_period_days),
                    self.custom_aggregation_filter(transfer))

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    def __init__(self,
                 name: str,
                 applied_to_transfer_types: AppliedToTypes,
                 application_filter: Callable,
                 time_period_days: int,
                 aggregation_filter: Optional[Query.filter] = matching_transfer_type_filter
                 ):
        self.name = name

        # Force to list of tuples to ensure the use of 'in' behaves as expected
        self.applied_to_transfer_types = [tuple(t) if isinstance(t, list) else t for t in applied_to_transfer_types]

        self.application_filter = application_filter
        self.time_period_days = time_period_days
        # TODO: Make LIMIT_EXCHANGE_RATE configurable per org
        self.custom_aggregation_filter = aggregation_filter


class AmountLimit(TransferLimit):
    @abstractmethod
    def get_allowance(self, transfer: CreditTransfer) -> TransferAmount:
        pass


class TotalAmountLimit(AmountLimit):

    def validate_transfer(self, transfer: CreditTransfer):
        allowance = self.get_allowance(transfer)
        if allowance < int(transfer.transfer_amount):
            message = 'Account Limit "{}" reached. {} available'.format(self.name, max(allowance, 0))

            raise TransferAmountLimitError(
                transfer_amount_limit=self.total_amount,
                transfer_amount_avail=allowance,
                limit_time_period_days=self.time_period_days,
                token=transfer.token.name,
                message=message
            )

    def get_allowance(self, transfer: CreditTransfer):
        return self.total_amount - self._aggregate_transfers(transfer)

    def _aggregate_transfers(self, transfer: CreditTransfer):
        # We need to sub the own transfer amount to the allowance because it's hard to exclude it from the aggregation
        return self._aggregate_transfer_query(
            transfer,
            db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
        ).execution_options(show_all=True).first().total - int(transfer.transfer_amount) or 0

    def __init__(
            self,
            name: str,
            applied_to_transfer_types: AppliedToTypes,
            application_filter: Callable,
            time_period_days: int,
            total_amount: int,
            aggregation_filter: Optional[Query.filter] = matching_transfer_type_filter
    ):
        super().__init__(
            name,
            applied_to_transfer_types,
            application_filter,
            time_period_days,
            aggregation_filter
        )

        self.total_amount = int(total_amount * config.LIMIT_EXCHANGE_RATE)


class MinimumSentLimit(AmountLimit):

    def validate_transfer(self, transfer: CreditTransfer):
        allowance = self.get_allowance(transfer)
        if allowance < int(transfer.transfer_amount):
            message = 'Account Limit "{}" reached. {} available'.format(self.name, max(allowance, 0))

            raise MinimumSentLimitError(
                transfer_amount_limit=self._aggregate_sent(transfer),
                transfer_amount_avail=allowance,
                limit_time_period_days=self.time_period_days,
                token=transfer.token.name,
                message=message
            )

    def get_allowance(self, transfer: CreditTransfer):
        return self._aggregate_sent(transfer) - self._aggregate_transfers(transfer)

    def _aggregate_transfers(self, transfer: CreditTransfer):
        return self._aggregate_transfer_query(
            transfer,
            db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
        ).execution_options(show_all=True).first().total or 0

    def _aggregate_sent(self, transfer: CreditTransfer):
        return pipe(
            db.session.query(func.sum(CreditTransfer.transfer_amount).label('total')),
            matching_sender_user_filter(transfer),
            not_rejected_filter,
            after_time_period_filter(self.time_period_days),
            regular_payment_filter
        ).execution_options(show_all=True).first().total or 0

    def __init__(
            self,
            name: str,
            applied_to_transfer_types: AppliedToTypes,
            application_filter: Callable,
            time_period_days: int,
            aggregation_filter: Optional[Query.filter] = matching_transfer_type_filter
    ):
        super().__init__(
            name,
            applied_to_transfer_types,
            application_filter,
            time_period_days,
            aggregation_filter
        )


class BalanceFractionLimit(AmountLimit):

    def validate_transfer(self, transfer: CreditTransfer):
        allowance = self.get_allowance(transfer)
        if allowance < transfer.transfer_amount:
            message = 'Account % Limit "{}" reached. {} available'.format(
                self.name,
                max(allowance, 0)
            )
            raise TransferBalanceFractionLimitError(
                transfer_balance_fraction_limit=self.balance_fraction,
                transfer_amount_avail=int(allowance),
                limit_time_period_days=self.time_period_days,
                token=transfer.token.name,
                message=message
            )

    def get_allowance(self, transfer: CreditTransfer):
        return self.balance_fraction * transfer.sender_transfer_account.balance

    def __init__(
            self,
            name: str,
            applied_to_transfer_types: AppliedToTypes,
            application_filter: Callable,
            time_period_days: int,
            balance_fraction: float,
            aggregation_filter: Optional[Query.filter] = matching_transfer_type_filter

    ):
        super().__init__(
            name,
            applied_to_transfer_types,
            application_filter,
            time_period_days,
            aggregation_filter
        )

        self.balance_fraction = balance_fraction


class TransferCountLimit(TransferLimit):

    def validate_transfer(self, transfer: CreditTransfer):
        allowance = self.get_allowance(transfer)

        if allowance <= 0:
            message = 'Account Limit "{}" reached. Allowed {} transaction per {} days' \
                .format(self.name, self.transfer_count, self.time_period_days)
            raise TransferCountLimitError(
                transfer_count_limit=self.transfer_count,
                limit_time_period_days=self.time_period_days,
                token=transfer.token.name,
                message=message
            )

    def get_allowance(self, transfer: CreditTransfer) -> int:
        return self.transfer_count - self._aggregate_transfers(transfer)

    def _aggregate_transfers(self, transfer: CreditTransfer):
        return self._aggregate_transfer_query(
            transfer,
            db.session.query(func.count(CreditTransfer.id).label('count'))
        ).execution_options(show_all=True).first().count - 1

    def __init__(
            self,
            name: str,
            applied_to_transfer_types: AppliedToTypes,
            application_filter: Callable,
            time_period_days: int,
            transfer_count: int,
            aggregation_filter: Optional[Query.filter] = matching_transfer_type_filter
    ):
        super().__init__(
            name,
            applied_to_transfer_types,
            application_filter,
            time_period_days,
            aggregation_filter
        )

        self.transfer_count = transfer_count


class NoTransferAllowedLimit(TransferLimit):

    def validate_transfer(self, transfer: CreditTransfer):
        raise NoTransferAllowedLimitError(token=transfer.token.name)

    def get_allowance(self, transfer: CreditTransfer) -> None:
        return None

    def __init__(
            self,
            name: str,
            applied_to_transfer_types: AppliedToTypes,
            application_filter: Callable,
    ):
        super().__init__(
            name,
            applied_to_transfer_types,
            application_filter,
            0
        )


# class ContextualisedLimit(object):
#     """
#     Binds a transfer to a limit, so that get_allowance can be easily accessed
#     """
#
#     def get_allowance(self) -> Union[int, TransferAmount]:
#         return self.limit.get_allowance(self.transfer)
#
#     def __init__(self, limit: TransferLimit, transfer: CreditTransfer):
#         self.limit = limit
#         self.transfer = transfer
#


LIMITS = [
    TotalAmountLimit('Sempo Level 0: P7', GENERAL_PAYMENTS,
                     is_any_token_and_user_is_not_phone_and_not_kyc_verified, 7,
                     total_amount=config.TRANSFER_LIMITS['0.P7']),
    TotalAmountLimit('Sempo Level 0: P30', GENERAL_PAYMENTS,
                     is_any_token_and_user_is_not_phone_and_not_kyc_verified, 30,
                     total_amount=config.TRANSFER_LIMITS['0.P30']),

    NoTransferAllowedLimit('Sempo Level 0: WD30', [WITHDRAWAL, DEPOSIT],
                           is_any_token_and_user_is_not_phone_and_not_kyc_verified),

    TotalAmountLimit('Sempo Level 1: P7', GENERAL_PAYMENTS,
                     is_any_token_and_user_is_phone_but_not_kyc_verified, 7,
                     total_amount=config.TRANSFER_LIMITS['1.P7']),
    TotalAmountLimit('Sempo Level 1: P30', GENERAL_PAYMENTS,
                     is_any_token_and_user_is_phone_but_not_kyc_verified, 30,
                     total_amount=config.TRANSFER_LIMITS['1.P30']),
    NoTransferAllowedLimit('Sempo Level 1: WD30', [WITHDRAWAL, DEPOSIT],
                           is_any_token_and_user_is_phone_but_not_kyc_verified),

    TotalAmountLimit('Sempo Level 2: P7', GENERAL_PAYMENTS,
                     is_any_token_and_user_is_kyc_verified, 7,
                     total_amount=config.TRANSFER_LIMITS['2.P7']),
    TotalAmountLimit('Sempo Level 2: P30', GENERAL_PAYMENTS,
                     is_any_token_and_user_is_kyc_verified, 30,
                     total_amount=config.TRANSFER_LIMITS['2.P30']),
    TotalAmountLimit('Sempo Level 2: WD7', [WITHDRAWAL, DEPOSIT],
                     is_any_token_and_user_is_kyc_verified, 7,
                     total_amount=config.TRANSFER_LIMITS['2.WD7']),
    TotalAmountLimit('Sempo Level 2: WD30', [WITHDRAWAL, DEPOSIT],
                     is_any_token_and_user_is_kyc_verified, 30,
                     total_amount=config.TRANSFER_LIMITS['2.WD30']),

    TotalAmountLimit('Sempo Level 3: P7', GENERAL_PAYMENTS,
                     is_any_token_and_user_is_kyc_business_verified, 7,
                     total_amount=config.TRANSFER_LIMITS['3.P7']),
    TotalAmountLimit('Sempo Level 3: P30', GENERAL_PAYMENTS,
                     is_any_token_and_user_is_kyc_business_verified, 30,
                     total_amount=config.TRANSFER_LIMITS['3.P30']),
    TotalAmountLimit('Sempo Level 3: WD7', [WITHDRAWAL, DEPOSIT],
                     is_any_token_and_user_is_kyc_business_verified, 7,
                     total_amount=config.TRANSFER_LIMITS['3.WD7']),
    TotalAmountLimit('Sempo Level 3: WD30', [WITHDRAWAL, DEPOSIT],
                     is_any_token_and_user_is_kyc_business_verified, 30,
                     total_amount=config.TRANSFER_LIMITS['3.WD30']),

    NoTransferAllowedLimit('GE Liquid Token - Standard User',
                           [AGENT_OUT_PAYMENT, WITHDRAWAL],
                           is_user_and_liquid_token),

    TransferCountLimit('GE Liquid Token - Group Account User',
                       [AGENT_OUT_PAYMENT, WITHDRAWAL],
                       is_group_and_liquid_token, 30,
                       aggregation_filter=withdrawal_or_agent_out_and_not_excluded_filter,
                       transfer_count=1),

    BalanceFractionLimit('GE Liquid Token - Group Account User',
                         [AGENT_OUT_PAYMENT, WITHDRAWAL],
                         is_group_and_liquid_token, 30,
                         aggregation_filter=withdrawal_or_agent_out_and_not_excluded_filter,
                         balance_fraction=0.50)
]
