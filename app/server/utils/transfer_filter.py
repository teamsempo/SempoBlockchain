import enum

MALE = 'male'
FEMALE = 'female'

BENEFICIARY = 'Beneficiary'
VENDOR = 'Vendor'
TOKEN_AGENT = 'Token Agent'
GROUP_ACCOUNT = 'Group Account'
ADMIN = 'Admin'
        

class TransferFilterEnum:
    INT_RANGE       = "int_range"
    DATE_RANGE      = 'date_range'
    DISCRETE        = "discrete"

TRANSFER_FILTERS = {
    'created': {
        'table': 'user',
        'type' : TransferFilterEnum.DATE_RANGE,
    },
    'User Type': {
        'table': 'user',
        'type': TransferFilterEnum.DISCRETE,
        'values': [BENEFICIARY, VENDOR, TOKEN_AGENT, GROUP_ACCOUNT, ADMIN]
    },
    'gender': {
        'table': 'custom_attribute_user_storage',
        'type': TransferFilterEnum.DISCRETE,
        'values' : [MALE, FEMALE]
    },
    'balance': {
        'table': 'transfer_account',
        'type' : TransferFilterEnum.INT_RANGE
    }
}

def process_transfer_filters():
    # parse and prepare filters for calculating transfer stats
    return
