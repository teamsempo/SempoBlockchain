import datetime
from functools import reduce
from typing import List

from sqlalchemy import or_

from server.models.credit_transfer import CreditTransfer
from server.utils.transfer_enums import TransferSubTypeEnum, TransferTypeEnum, TransferStatusEnum


def combine_filter_lists(filter_lists: List[List]) -> List:
    return reduce(lambda f, i: f + i, filter_lists, [])


def after_time_period_filter(days: int):
    epoch = datetime.datetime.today() - datetime.timedelta(days=days)
    return [CreditTransfer.created >= epoch]


def matching_sender_user_filter(transfer: CreditTransfer):
    return [CreditTransfer.sender_user == transfer.sender_user]


def regular_payment_filter(transfer: CreditTransfer):
    return [CreditTransfer.transfer_subtype == TransferSubTypeEnum.STANDARD]


def matching_transfer_type_filter(transfer: CreditTransfer):
    return [CreditTransfer.transfer_type == transfer.transfer_type]


def matching_transfer_type_and_subtype_filter(transfer: CreditTransfer):
    return [
        CreditTransfer.transfer_type == transfer.transfer_type,
        CreditTransfer.transfer_subtype == transfer.transfer_subtype
    ]


def withdrawal_or_agent_out_and_not_excluded_filter(transfer: CreditTransfer):
    return [
        or_(CreditTransfer.transfer_type == TransferTypeEnum.WITHDRAWAL,
            CreditTransfer.transfer_subtype == TransferSubTypeEnum.AGENT_OUT),
        CreditTransfer.exclude_from_limit_calcs == False
    ]


def not_rejected_filter():
    return [CreditTransfer.transfer_status != TransferStatusEnum.REJECTED]