class AccountLimitError(Exception):
    """
    Raise if account limits have been reached when transfer is attempted
    """
    pass


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
