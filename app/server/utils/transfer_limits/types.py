from typing import List, Union, Tuple, Callable

from sqlalchemy.orm import Query

from server.models.credit_transfer import CreditTransfer
from server.sempo_types import TransferAmount
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum

AppliedToTypes = List[Union[TransferTypeEnum, Tuple[TransferTypeEnum, TransferSubTypeEnum]]]

AggregateAvailability = Union[int, TransferAmount]

ApplicationFilter = Callable[[CreditTransfer], bool]

AggregationFilter = Callable[[CreditTransfer], list]

QueryConstructorFunc = Callable[[CreditTransfer, Query], Query]
