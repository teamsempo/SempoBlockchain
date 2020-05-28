from typing import List, Union, Tuple, Callable

from sqlalchemy.orm import Query

from server.models.credit_transfer import CreditTransfer
from server.sempo_types import TransferAmount
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum

# A list of transfer types/subtypes that a limit may apply to. Can either be a Type, in which case
# all limits with the same type will match (for example all Exchanges) regardless of subtype
# or a (Type, Subtype) tuple, in which case the limit will match only if it shares the exact type and subtype.
AppliedToTypes = List[Union[TransferTypeEnum, Tuple[TransferTypeEnum, TransferSubTypeEnum]]]

# Used when the availability is some numerical amount, such as transfer count or an amount.
NumericAvailability = Union[int, TransferAmount]

# Used to define whether a transfer applies to a particular limit.
# Takes a CreditTransfer object and returns 'false' if the transfer doesn't satisfy the particular criteria
ApplicationFilter = Callable[[CreditTransfer], bool]

# Passed into an SQLAlchemy filter object to filter transfers for aggregating some count amount
AggregationFilter = Callable[[CreditTransfer], list]

# Used to construct the SQLAlchemy Query used for aggregation purposes
QueryConstructorFunc = Callable[[CreditTransfer, Query], Query]
