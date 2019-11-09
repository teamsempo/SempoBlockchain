
class PreBlockchainError(Exception):
    """Error before transaction sent to blockchain"""
    def __init__(self, message, is_logged):
        super().__init__(message)

        # Now for your custom code...
        self.is_logged = is_logged

class WrongContractNameError(Exception):
    """Unexpected contract name"""

class WalletExistsError(Exception):
    """Unexpected contract name"""