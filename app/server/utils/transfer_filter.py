import enum

MALE = 'Male'
FEMALE = 'Female'

BENEFICIARY = 'Beneficiary'
VENDOR = 'Vendor'
TOKEN_AGENT = 'Token Agent'
GROUP_ACCOUNT = 'Group Account'
ADMIN = 'Admin'
        

class TransferFilterEnum:
    INT_RANGE       = "int_range"
    DATE_RANGE      = 'date_range'
    DISCRETE        = "discrete"

TRANSFER_FILTERS = [
    {
        'field': 'Created',
        'table': 'user',
        'type' : TransferFilterEnum.DATE_RANGE,
    },
    {
        'field': 'User Type',
        'table': 'user',
        'type': TransferFilterEnum.DISCRETE,
        'values': [BENEFICIARY, VENDOR, TOKEN_AGENT, GROUP_ACCOUNT, ADMIN]
    },
    {
        'field': 'Gender',
        'table': 'custom_attribute_user_storage',
        'type': TransferFilterEnum.DISCRETE,
        'values' : [MALE, FEMALE]
    },
    {
        'field': 'Balance',
        'table': 'transfer_account',
        'type' : TransferFilterEnum.INT_RANGE
    }
]

def process_transfer_filters():
    # parse and prepare filters for calculating transfer stats
    return
