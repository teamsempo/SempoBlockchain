import enum
from sqlalchemy.sql import text

MALE = 'male'
FEMALE = 'female'

BENEFICIARY = 'Beneficiary'
VENDOR = 'Vendor'
TOKEN_AGENT = 'Token Agent'
GROUP_ACCOUNT = 'Group Account'
ADMIN = 'Admin'

USER_TABLE = 'user'
CUSTOM_ATTRIBUTE_USER_STORAGE = 'custom_attribute_user_storage'
TRANSFER_ACCOUNT_TABLE = 'transfer_account'
        

class TransferFilterEnum:
    INT_RANGE       = "int_range"
    DATE_RANGE      = 'date_range'
    DISCRETE        = "discrete"

TRANSFER_FILTERS = {
    'created': {
        'table': USER_TABLE,
        'type' : TransferFilterEnum.DATE_RANGE,
    },
    'User Type': {
        'table': USER_TABLE,
        'type': TransferFilterEnum.DISCRETE,
        'values': [BENEFICIARY, VENDOR, TOKEN_AGENT, GROUP_ACCOUNT, ADMIN]
    },
    'gender': {
        'table': CUSTOM_ATTRIBUTE_USER_STORAGE,
        'type': TransferFilterEnum.DISCRETE,
        'values' : [MALE, FEMALE]
    },
    'balance': {
        'table': TRANSFER_ACCOUNT_TABLE,
        'type' : TransferFilterEnum.INT_RANGE
    }
}

def process_transfer_filters(encoded_filters):
    # parse and prepare filters for calculating transfer stats
    tokenized_filters = encoded_filters.split("%")
    filters = []
    curr_keyName = None

    to_handle = []
    for item in tokenized_filters:
        if item is not None and len(item) > 0:
            symbol = item[:1]
            subject = item[1:]
            if symbol == ",":

                # handle currently collected filters
                if len(to_handle) > 0 and (curr_keyName is not None):
                    if(TRANSFER_FILTERS[curr_keyName]['table'] == CUSTOM_ATTRIBUTE_USER_STORAGE):
                        filters.append(handle_custom_user_storage_filter(curr_keyName, to_handle))
                    else:
                        filters.append(handle_filter(curr_keyName, to_handle))

                curr_keyName = None
                if subject in TRANSFER_FILTERS:
                    to_handle = []
                    curr_keyName = subject
            if (symbol == "=" or symbol == "<" or symbol == ">"):
                to_handle.append({
                    'comparator': symbol,
                    'value': subject
                })

    # handle currently collected filters
    if len(to_handle) > 0 and (curr_keyName is not None):
        if(TRANSFER_FILTERS[curr_keyName]['table'] == CUSTOM_ATTRIBUTE_USER_STORAGE):
            filters.append(handle_custom_user_storage_filter(curr_keyName, to_handle))
        else:
            filters.append(handle_filter(curr_keyName, to_handle))

    print(filters)

    return filters

def handle_custom_user_storage_filter(keyname, filters):
    filter_string = ""
    for i, filter_action in enumerate(filters):
        comparator = filter_action['comparator']
        value = filter_action['value']
        filter_string += f"{'OR' if i > 0 else ''} \"{TRANSFER_FILTERS[keyname]['table']}\".value {comparator} '\"{value}\"' "
    print(filter_string)

    return text(filter_string)

def handle_filter(keyname, filters):
    filter_string = ""
    for filter_action in filters:
        comparator = filter_action['comparator']
        value = filter_action['value']
        filter_string += f" \"{TRANSFER_FILTERS[keyname]['table']}\".{keyname} {comparator} {value}"
    return text(filter_string)

