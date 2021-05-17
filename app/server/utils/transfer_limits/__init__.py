# Limits used to work out if a transfer requested by a particular user is allowable or othewise
# for example due to KYC restrictions
# The standard limits we use are defined below in LIMIT_IMPLEMENTATIONS
# Use the BaseTransferLimit or the other subclasses to add your own

from typing import List
import config
from decimal import Decimal

from server.models.credit_transfer import CreditTransfer
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum
from server.utils.transfer_limits.checks import (
    is_any_token_and_user_is_not_phone_and_not_kyc_verified,
    is_any_token_and_user_is_phone_but_not_kyc_verified,
    is_any_token_and_user_is_kyc_verified,
    is_any_token_and_user_is_kyc_business_verified,
    is_user_and_liquid_token, is_group_and_liquid_token
)
from server.utils.transfer_limits.filters import (
    withdrawal_or_agent_out_and_not_excluded_filter
)
from server.utils.transfer_limits.limits import (
    TotalAmountLimit,
    NoTransferAllowedLimit,
    TransferCountLimit,
    BalanceFractionLimit,
    MinimumSentLimit,
    MaximumAmountPerTransferLimit,
    BaseTransferLimit
)


def get_applicable_transfer_limits(
        candidate_limits: List[BaseTransferLimit],
        transfer: CreditTransfer
) -> List[BaseTransferLimit]:
    """
    Convenience function filtering a list of limits to find the ones that apply to a transfer

    :param candidate_limits: the set of limits to filter
    :param transfer: the transfer to test for applicability
    :return: a list of the limits that do apply
    """
    return [limit for limit in candidate_limits if limit.applies_to_transfer(transfer)]


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


LIMIT_IMPLEMENTATIONS = [
]