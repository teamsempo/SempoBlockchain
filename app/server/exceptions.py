class UserTransferAccountDeletionError(Exception):
    """
    Raise if User default doesn't match Transfer Account primary user OR more than 1 user is listed on Transfer Account
    """
    pass


class ResourceAlreadyDeletedError(Exception):
    """
    Raise if User or Transfer Account is already deleted
    """
    pass


class TransferLimitCreationError(Exception):
    """
    Raise if a TransferLimit is initialized with incorrect variables
    """
    pass


class AccountLimitError(Exception):
    """
    Raise if account LIMITS have been reached when transfer is attempted
    """
    def __init__(self, message: str, limit_time_period_days: int, token: str):
        self.message = message
        self.limit_time_period_days = limit_time_period_days
        self.token = token

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message

class NoTransferAllowedLimitError(AccountLimitError):
    def __init__(self, token):
        super().__init__(message='No transfers are allowed', limit_time_period_days=0, token=token)

class TransferCountLimitError(AccountLimitError):
    def __init__(self, transfer_count_limit: int, **kwargs):
        super().__init__(**kwargs)
        self.transfer_count_limit = transfer_count_limit


class TransferBalanceFractionLimitError(AccountLimitError):
    def __init__(self, transfer_balance_fraction_limit: float, transfer_amount_avail: int, **kwargs):
        super().__init__(**kwargs)
        self.transfer_balance_fraction_limit = transfer_balance_fraction_limit
        self.transfer_amount_avail = transfer_amount_avail


class TransferAmountLimitError(AccountLimitError):
    def __init__(self, transfer_amount_limit: int, transfer_amount_avail: int, **kwargs):
        super().__init__(**kwargs)
        self.transfer_amount_limit = transfer_amount_limit
        self.transfer_amount_avail = transfer_amount_avail


class NameScanException(Exception):
    """
    Raise if namescan api returns an error
    """
    pass


class PaymentMethodException(Exception):
    """
    Raise if trying to set a payment method that is not supported
    """
    pass


class OrganisationNotProvidedException(Exception):
    """
    Raise if trying to query database without providing an organisation ID or SHOW_ALL flag.
    """
    pass


class IconNotSupportedException(Exception):
    """
    Raise if trying to set TransferUsage to an icon not supported on mobile (currently only MaterialCommunityIcons)
    """


class TransferUsageNameDuplicateException(Exception):
    """
    Raise if trying to set the name of TransferUsage to a name that already exists in the table
    """


class TypeNotFoundException(Exception):
    """
    Raise if trying to set kyc application type to type that does not exist
    """
    pass


class TierNotFoundException(Exception):
    """
    Raise if trying reference role tier that does not exist
    """
    pass


class RoleNotFoundException(Exception):
    """
    Raise if trying reference role that does not exist
    """
    pass


class InvalidTransferTypeException(Exception):
    """
    Raise if the transfer type string isn't one of the enumerated transfer types
    """
    pass


class InsufficientBalanceException(Exception):
    """
    Raise if the transfer account doesn't have sufficient balance to make the transfer
    """
    pass


class NoTransferAccountError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class InsufficientBalanceError(Exception):
    pass

class SubexchangeNotFound(Exception):
    pass

class AccountNotApprovedError(Exception):
    def __init__(self, message, is_sender=None):
        self.message = message
        self.is_sender = is_sender

    def __repr__(self):
        return self.message


class InvalidTargetBalanceError(Exception):
    pass


class BlockchainError(Exception):
    pass


class NoTransferCardError(Exception):
    pass


class PhoneVerificationError(Exception):
    pass


class TransferAccountNotFoundError(Exception):
    pass