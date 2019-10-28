import enum

class TransferTypeEnum(enum.Enum):
    PAYMENT     = "PAYMENT"
    DEPOSIT     = "DEPOSIT"
    WITHDRAWAL  = "WITHDRAWAL"
    EXCHANGE    = "EXCHANGE"
    FEE         = "FEE"

class TransferModeEnum(enum.Enum):
    NFC = "NFC"
    SMS = "SMS"
    QR  = "QR"
    INTERNAL = "INTERNAL"
    OTHER    = "OTHER"

class TransferStatusEnum(enum.Enum):
    PENDING = 'PENDING'
    REJECTED = 'REJECTED'
    COMPLETE = 'COMPLETE'
    # PENDING = 0
    # INTERNAL_REJECTED = -1
    # INTERNAL_COMPLETE = 1
    # BLOCKCHAIN_REJECTED = -2
    # BLOCKCHAIN_COMPLETE = 2

#TODO add an enum for blockchain status