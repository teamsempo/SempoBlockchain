from abc import ABC, abstractmethod
from sqlalchemy import func
from sqlalchemy.orm import Query
from decimal import Decimal

import config
from server import db
from server.exceptions import (
    NoTransferAllowedLimitError,
    MaximumPerTransferLimitError,
    TransferAmountLimitError,
    MinimumSentLimitError,
    TransferBalanceFractionLimitError,
    TransferCountLimitError
)
from server.models.credit_transfer import CreditTransfer
from server.sempo_types import TransferAmount
from server.utils.transfer_limits.filters import (
    combine_filter_lists,
    matching_sender_user_filter,
    not_rejected_filter,
    after_time_period_filter,
    matching_transfer_type_filter,
    regular_payment_filter
)
from server.utils.transfer_limits.types import (
    NumericAvailability,
    AppliedToTypes,
    ApplicationFilter,
    QueryConstructorFunc,
    AggregationFilter
)


class BaseTransferLimit(ABC):
    """
    Base Limit Class. All limits use `applies_to_transfer` to determine if they are applied.
    Specific Limit rules vary hugely, so this class is pretty sparse,
    however, the usage of all limits follows the same overall process:

    1. Check if the limit applies to the transfer
       This is done using `applies_to_transfer`, and is  based off:
        a) Type/Subtype
        b) Query Filters

    2. Calculate how much of the limit is available, without considering this transfer
       This is done using `available`. This number may be fixed, though it often varies due to a base amount that is
       deducted from by aggregating across previous transfers and subtracting.
       See the AggregateLimit abstract class for an example of this.

    3. Calculate how much the current transfer cases uses
       This is done using `case_will_use`

    4. Check if the current case uses more than what's available
       This is done using `validate_transfer`. If there's insufficient availability, throw an exception
       that is appropriately subclassed from TransferLimitError


    While the above steps represent a typical "workflow", all the functions defined in this Abstract Class can and
    are called upon in other contexts outside of pure validation, for example to tell a user how much of a limit
    is remaining for them.
    These methods can be overridden as required. See NoTransferAllowedLimit for an example of this.

    All methods require a CreditTransfer object, as this contains the full context of amount, senders, recipients
    and so forth to fully determine how to apply the limit
    """

    @abstractmethod
    def available(self, transfer: CreditTransfer) -> NumericAvailability:
        """
        How much of the limit is still available. Uses a CreditTransfer object for context.
        Is generally an amount, but can also be something like a number of transfers.
        :param transfer: the transfer in question
        :return: Count or Amount
        """
        pass

    @abstractmethod
    def case_will_use(self, transfer: CreditTransfer) -> NumericAvailability:
        """
        How much of the limit will be used in this particular transfer case.
        Is generally an amount, but can also be something like a number of transfers.
        :param transfer: the transfer in question
        :return: count or TransferAmount
        """

    @abstractmethod
    def throw_validation_error(self, transfer: CreditTransfer, available: NumericAvailability):
        """
        Throws some sort of TransferLimitError
        """
        pass

    def validate_transfer(self, transfer: CreditTransfer):
        """
        Will raise an exception if the provided transfer doesn't pass this limit
        :param transfer: the transfer you wish to validate
        :return: Nothing, just throws the appropriate error if the transfer doesn't pass
        """

        available = self.available(transfer)
        if available < self.case_will_use(transfer):
            self.throw_validation_error(transfer, available)

    def applies_to_transfer(self, transfer: CreditTransfer) -> bool:
        """
        Determines if the limit applies to the given transfer. Uses a two step process:

        - Include transfer only if it matches either a Type or a (Type,Subtype) tuple from applied_to_transfer_types
        - Include transfer only if calling `application_filter` on the transfer returns true

        :param transfer: the credit transfer in question
        :return: boolean of whether the limit is applied or not
        """
        return (
                       transfer.transfer_type in self.applied_to_transfer_types
                       or (transfer.transfer_type, transfer.transfer_subtype) in self.applied_to_transfer_types
               ) and self.application_filter(transfer)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    def __init__(self,
                 name: str,
                 applied_to_transfer_types: AppliedToTypes,
                 application_filter: ApplicationFilter,
                 ):
        """
        :param name: Human-friendly name
        :param applied_to_transfer_types: list which each item is either a
         TransferType or a (TransferType ,TransferSubType) tuple
        :param application_filter: one of the base or composite checks listed at the top of this file
        """

        self.name = name

        # Force to list of tuples to ensure the use of 'in' behaves as expected
        self.applied_to_transfer_types = [tuple(t) if isinstance(t, list) else t for t in applied_to_transfer_types]
        self.application_filter = application_filter


class NoTransferAllowedLimit(BaseTransferLimit):
    """
    A special limit that always throws a 'NoTransferAllowedLimitError' exception when `validate_transfer` is called.
    Includes an example of overriding `validate_transfer` as the usual rule doesn't really apply
    """

    def available(self, transfer: CreditTransfer) -> NumericAvailability:
        return 0

    def case_will_use(self, transfer: CreditTransfer) -> None:
        return None

    def validate_transfer(self, transfer: CreditTransfer):
        available = self.available(transfer)
        self.throw_validation_error(transfer, available)

    def throw_validation_error(self, transfer: CreditTransfer, available: NumericAvailability):
        raise NoTransferAllowedLimitError(token=transfer.token.name)

    def __init__(
            self,
            name: str,
            applied_to_transfer_types: AppliedToTypes,
            application_filter: ApplicationFilter,
    ):
        super().__init__(
            name,
            applied_to_transfer_types,
            application_filter
        )


class MaximumAmountPerTransferLimit(BaseTransferLimit):
    """
    A limit that specifies a maximum amount that can be transferred per transfer
    """

    def available(self, transfer: CreditTransfer) -> NumericAvailability:
        return self.maximum_amount

    def case_will_use(self, transfer: CreditTransfer) -> NumericAvailability:
        return transfer.transfer_amount

    def throw_validation_error(self, transfer: CreditTransfer, available: NumericAvailability):
        message = 'Maximum Per Transfer Exceeded (Limit {}). {} available'.format(self.name, self.maximum_amount)

        raise MaximumPerTransferLimitError(
            message=message,
            maximum_amount_limit=self.maximum_amount,
            token=transfer.token.name)

    def __init__(
            self,
            name: str,
            applied_to_transfer_types: AppliedToTypes,
            application_filter: ApplicationFilter,
            maximum_amount: TransferAmount
    ):
        super().__init__(
            name,
            applied_to_transfer_types,
            application_filter,
        )

        self.maximum_amount = int(maximum_amount * config.LIMIT_EXCHANGE_RATE)


class AggregateLimit(BaseTransferLimit):
    """
    A transfer limit that uses an aggregate (count, total sent etc) of previous transfers over some time period
    for its available amount criteria.
    """

    @abstractmethod
    def available_base(self, transfer: CreditTransfer) -> NumericAvailability:
        """
        Calculate how much base availability there is for the limit,
        before historical transactions are taken into account
        :param transfer: the credit transfer in question
        :return: Either a transfer amount or a count
        """
        pass

    @abstractmethod
    def used_aggregator(
            self,
            transfer: CreditTransfer,
            query_constructor: QueryConstructorFunc
    ) -> NumericAvailability:
        """
        The aggregator function is used to calculate the how much of the availability has been consumed.
        Takes the query_constructor as an input rather than accessing via 'self' as it allows us to easily create
        mixins for various types of aggregation (for example total transfer amounts).
        :param transfer: the credit transfer in question
        :param query_constructor: the query constructor as defined below.
        :return: Either a transfer amount or transfer count
        """
        pass

    def available(self, transfer: CreditTransfer) -> NumericAvailability:
        base = self.available_base(transfer)
        used = self.used_aggregator(
            transfer,
            self.query_constructor
        )

        return base - used

    def query_constructor_filter_specifiable(
            self,
            transfer: CreditTransfer,
            base_query: Query,
            custom_filter: AggregationFilter) -> Query:
        """
        Constructs a filtered query for aggregation, where the last filter step can be provided by the user
        :param transfer:
        :param base_query:
        :param custom_filter:
        :return: An SQLAlchemy Query Object
        """

        filter_list = combine_filter_lists(
            [
                matching_sender_user_filter(transfer),
                not_rejected_filter(),
                after_time_period_filter(self.time_period_days),
                custom_filter(transfer)
            ]
        )

        return base_query.filter(*filter_list)

    def query_constructor(
            self,
            transfer: CreditTransfer,
            base_query: Query,
    ) -> Query:
        """
        Acts as a partial for `query_constructor_filter_specifiable`, with the custom aggregation filter set to that
        provided to the limit on instantiation. We don't use an actual partial because mypy type checking won't work.
        :param transfer:
        :param base_query:
        :return: An SQLAlchemy Query Object
        """

        return self.query_constructor_filter_specifiable(transfer, base_query, self.custom_aggregation_filter)

    def __init__(self,
                 name: str,
                 applied_to_transfer_types: AppliedToTypes,
                 application_filter: ApplicationFilter,
                 time_period_days: int,
                 aggregation_filter: AggregationFilter = matching_transfer_type_filter
                 ):
        """
        :param name:
        :param applied_to_transfer_types:
        :param application_filter:
        :param time_period_days: How many days back to include in aggregation
        :param aggregation_filter: An SQLAlchemy Query Filter
        """

        super().__init__(name, applied_to_transfer_types, application_filter)

        self.time_period_days = time_period_days

        self.custom_aggregation_filter = aggregation_filter


class AggregateTransferAmountMixin(object):
    """
    A Mixin for aggregating over transfer amounts. Use it alongside the AggregateLimit class
    """

    @staticmethod
    def used_aggregator(transfer: CreditTransfer, query_constructor: QueryConstructorFunc):
        # We need to sub the transfer amount from the allowance because it's hard to exclude it from the aggregation
        allowance = query_constructor(
            transfer,
            db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
        ).execution_options(show_all=True).first().total or 0
        return allowance - int(transfer.transfer_amount)

    @staticmethod
    def case_will_use(transfer: CreditTransfer) -> TransferAmount:
        return transfer.transfer_amount


class TotalAmountLimit(AggregateTransferAmountMixin, AggregateLimit):
    """
    A limit that where the maxium amount that can be transferred over a set of transfers within a time period is fixed.
    Eg "You can transfer a maximum of 400 Foo token every 10 days"
    """

    def available_base(self, transfer: CreditTransfer) -> TransferAmount:
        return self._total_amount

    def throw_validation_error(self, transfer: CreditTransfer, available: NumericAvailability):
        message = 'Account Limit "{}" reached. {} available'.format(self.name, max(available, 0))

        raise TransferAmountLimitError(
            transfer_amount_limit=self.available_base(transfer),
            transfer_amount_avail=available,
            limit_time_period_days=self.time_period_days,
            token=transfer.token.name,
            message=message
        )

    def __init__(
            self,
            name: str,
            applied_to_transfer_types: AppliedToTypes,
            application_filter: ApplicationFilter,
            time_period_days: int,
            total_amount: TransferAmount,
            aggregation_filter: AggregationFilter = matching_transfer_type_filter
    ):
        super().__init__(
            name,
            applied_to_transfer_types,
            application_filter,
            time_period_days,
            aggregation_filter
        )

        # TODO: Make LIMIT_EXCHANGE_RATE configurable per org
        self._total_amount: TransferAmount = int(total_amount * config.LIMIT_EXCHANGE_RATE)


class MinimumSentLimit(AggregateTransferAmountMixin, AggregateLimit):
    """
    A limit that where the maximum amount that can be transferred over a set of transfers within a time period must be
    less than the amount sent of some other transfer type (defaults to regular payments) in that same time period
    Eg "You have made 300 FooTokens worth of payments in the last 7 days, so you can make a maximum of 300 Footokens
    worth of withdrawals"
    """

    def available_base(self, transfer: CreditTransfer) -> TransferAmount:
        return self.query_constructor_filter_specifiable(
            transfer,
            db.session.query(func.sum(CreditTransfer.transfer_amount).label('total')),
            self.minimum_sent_aggregation_filter
        ).execution_options(show_all=True).first().total or 0

    def throw_validation_error(self, transfer: CreditTransfer, available: NumericAvailability):
        message = 'Account Limit "{}" reached. {} available'.format(self.name, max(int(available), 0))

        raise MinimumSentLimitError(
            transfer_amount_limit=self.available_base(transfer),
            transfer_amount_avail=available,
            limit_time_period_days=self.time_period_days,
            token=transfer.token.name,
            message=message
        )

    def __init__(
            self,
            name: str,
            applied_to_transfer_types: AppliedToTypes,
            application_filter: ApplicationFilter,
            time_period_days: int,
            aggregation_filter: AggregationFilter = matching_transfer_type_filter,
            minimum_sent_aggregation_filter: AggregationFilter = regular_payment_filter
    ):
        super().__init__(
            name,
            applied_to_transfer_types,
            application_filter,
            time_period_days,
            aggregation_filter
        )

        self.minimum_sent_aggregation_filter = minimum_sent_aggregation_filter


class BalanceFractionLimit(AggregateTransferAmountMixin, AggregateLimit):
    """
    A limit that where the maximum amount that can be transferred over a set of transfers within a time period must be
    less than some fraction of the balance of the user at that moment.
    Has slightly weird behaviour in that the limit can change a lot depending on the balance (that's the point)
    Eg "Your current balance is 500 FooTokens, you're allowed to withdrawl half in a 7 day period.
    """

    def available_base(self, transfer: CreditTransfer) -> TransferAmount:
        return self._total_from_balance(transfer.sender_transfer_account.balance)

    def _total_from_balance(self, balance: int) -> TransferAmount:
        amount: TransferAmount = int(self.balance_fraction * balance)
        return amount

    def throw_validation_error(self, transfer: CreditTransfer, available: NumericAvailability):
        message = 'Account % Limit "{}" reached. {} available'.format(
            self.name,
            max([available, 0])
        )
        raise TransferBalanceFractionLimitError(
            transfer_balance_fraction_limit=self.balance_fraction,
            transfer_amount_avail=available,
            limit_time_period_days=self.time_period_days,
            token=transfer.token.name,
            message=message
        )

    def __init__(
            self,
            name: str,
            applied_to_transfer_types: AppliedToTypes,
            application_filter: ApplicationFilter,
            time_period_days: int,
            balance_fraction: Decimal,
            aggregation_filter: AggregationFilter = matching_transfer_type_filter

    ):
        super().__init__(
            name,
            applied_to_transfer_types,
            application_filter,
            time_period_days,
            aggregation_filter
        )

        self.balance_fraction = balance_fraction


class TransferCountLimit(AggregateLimit):
    """
    An Aggregate Limit that limits based on the number of transfers made (rather than the amount transferred).
    If we end up making more variations of this, it may be worth creating a count mixin.
    """

    def used_aggregator(
            self,
            transfer: CreditTransfer,
            query_constructor: QueryConstructorFunc
    ) -> NumericAvailability:

        return query_constructor(
            transfer,
            db.session.query(func.count(CreditTransfer.id).label('count'))
        ).execution_options(show_all=True).first().count - 1

    def case_will_use(self, transfer: CreditTransfer) -> int:
        return 1

    def available_base(self, transfer: CreditTransfer) -> int:
        return self.transfer_count

    def throw_validation_error(self, transfer: CreditTransfer, available: NumericAvailability):
        message = 'Account Limit "{}" reached. Allowed {} transaction per {} days' \
            .format(self.name, self.transfer_count, self.time_period_days)
        raise TransferCountLimitError(
            transfer_count_limit=self.transfer_count,
            limit_time_period_days=self.time_period_days,
            token=transfer.token.name,
            message=message
        )

    def __init__(
            self,
            name: str,
            applied_to_transfer_types: AppliedToTypes,
            application_filter: ApplicationFilter,
            time_period_days: int,
            transfer_count: int,
            aggregation_filter: AggregationFilter = matching_transfer_type_filter
    ):
        super().__init__(
            name,
            applied_to_transfer_types,
            application_filter,
            time_period_days,
            aggregation_filter
        )

        self.transfer_count = transfer_count

