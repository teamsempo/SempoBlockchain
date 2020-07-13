
class PreBlockchainError(Exception):
    """Error before transaction sent to blockchain"""
    def __init__(self, message):
        super().__init__(message)

class WrongContractNameError(Exception):
    """Unexpected contract name"""

class WalletExistsError(Exception):
    """Wallet already exists for the address provided"""

class TaskRetriesExceededError(Exception):
    """Number of transaction retries allowed for task has been exceeded"""

class LockedNotAcquired(Exception):
    """Redis lock not acquired"""
    pass