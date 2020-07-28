# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

import enum
from sqlalchemy.sql import text
from sqlalchemy import or_, Column, String, Float
from server import db
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server.models.transfer_account import TransferAccount
from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from sqlalchemy.sql.expression import cast

MALE = 'male'
FEMALE = 'female'

BENEFICIARY = "Beneficiary"
VENDOR = "Vendor"
TOKEN_AGENT = "Token Agent"
GROUP_ACCOUNT = "Group Account"

BOOLEAN_MAPPINGS = {
    BENEFICIARY: "has_beneficiary_role",
    VENDOR: "has_vendor_role",
    TOKEN_AGENT: "has_token_agent_role",
    GROUP_ACCOUNT: "has_group_account_role"
}

class TransferFilterEnum:
    INT_RANGE       = "int_range"
    DATE_RANGE      = 'date_range'
    DISCRETE        = "discrete"
    BOOLEAN_MAPPING = "boolean_mapping"


ALL_FILTERS = {
    'transfer_amount': {
        'name': 'Transfer Amount',
        'table': CreditTransfer.__tablename__,
        'type': TransferFilterEnum.INT_RANGE
    },
    'created': {
        'name': "Created",
        'table': User.__tablename__,
        'type' : TransferFilterEnum.DATE_RANGE,
    },
    'user_type': {
        'name': "User Type",
        'table': User.__tablename__,
        'type': TransferFilterEnum.BOOLEAN_MAPPING,
        'values': [BENEFICIARY, VENDOR, TOKEN_AGENT, GROUP_ACCOUNT]
    },
    'gender': {
        'name': "Gender",
        'table': CustomAttributeUserStorage.__tablename__,
        'type': TransferFilterEnum.DISCRETE,
        'values' : [MALE, FEMALE]
    },
    'rounded_account_balance': {
        'name': "Balance",
        'table': TransferAccount.__tablename__,
        'type' : TransferFilterEnum.INT_RANGE
    }
}

TRANSFER_FILTERS = ALL_FILTERS

USER_FILTERS = {
    'created': ALL_FILTERS['created'],
    'user_type': ALL_FILTERS['user_type'],
    'gender': ALL_FILTERS['gender'],
    'rounded_account_balance': ALL_FILTERS['rounded_account_balance']
}

# will return a dictionary with table names as keys
# values will be a dictionary of array of tuples
# values on the outer array should be AND'd together

def process_transfer_filters(encoded_filters):
    # parse and prepare filters for calculating transfer stats
    if (encoded_filters is None):
        return

    filter_list = parse_filter_string(encoded_filters)

    filter_dict = {}

    for f in filter_list:

        unprocessed_attribute = f['attribute']
        table = ALL_FILTERS[unprocessed_attribute]['table']

        processed = handle_filter(**f)

        if table not in filter_dict:
            filter_dict[table] = []
        filter_dict[table].append(processed)

    return filter_dict


def parse_filter_string(filter_string):
    """
    Converts a filter string into a list of dictionary values
    """
    tokenized_filters = filter_string.split(":")

    filters = []
    for item in tokenized_filters:
        if item is not None and len(item) > 0:
            left_bracket_split = item.split('(')
            stripped_of_right_bracket = [s.strip(')') for s in left_bracket_split]

            attribute = stripped_of_right_bracket[0]
            comparator = stripped_of_right_bracket[1]
            value_list = stripped_of_right_bracket[2].split(',')

            if comparator == 'IN':
                value = value_list
            else:
                value = value_list[0]

            filters.append({
                'attribute': attribute,
                'comparator': comparator,
                'value': value
            })

    return filters


def handle_filter(attribute, comparator, value):
    if ALL_FILTERS[attribute]['type'] == TransferFilterEnum.BOOLEAN_MAPPING:
        return handle_boolean_mapping(attribute, comparator, value)

    elif ALL_FILTERS[attribute]['type'] == TransferFilterEnum.DISCRETE:
        return handle_discrete(attribute, comparator, value)
    else:
        return handle_other_types(attribute, comparator, value)


def handle_boolean_mapping(attribute, comparator, value):

    filters = []
    for v in value:
        attribute = BOOLEAN_MAPPINGS[v]
        filters.append((attribute, "EQ", True))

    return filters


def handle_discrete(attribute, comparator, value):
    return [(attribute, "EQ", value)]


def handle_other_types(attribute, comparator, value):
    value = value if ALL_FILTERS[attribute]['type'] == TransferFilterEnum.DATE_RANGE else float(value)
    return [(attribute, comparator, value)]

