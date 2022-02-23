import enum
from sqlalchemy.sql import text
from sqlalchemy import or_, Column, String, Float
from server import db
from server.models.custom_attribute import CustomAttribute, MetricsVisibility
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server.models.transfer_account import TransferAccount
from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum

BENEFICIARY = "Beneficiary"
VENDOR = "Vendor"
TOKEN_AGENT = "Token Agent"
GROUP_ACCOUNT = "Group Account"

SENDER = 'sender'
RECIPIENT = 'recipient'

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

def get_custom_attribute_filters(distinct_sender_and_recipient = False):
    # Get all custom attributes and options
    attribute_options = db.session.query(CustomAttribute)\
        .filter(CustomAttribute.filter_visibility != MetricsVisibility.HIDDEN)\
        .all()
    # Build those into filters objects
    filters = {}
    for ao in attribute_options:
        if distinct_sender_and_recipient:
            if ao.filter_visibility in [MetricsVisibility.SENDER_AND_RECIPIENT, MetricsVisibility.SENDER]:
                filters[ao.name + ',sender'] = {
                    'name': 'Sender ' + ao.name.capitalize(),
                    'table': CustomAttributeUserStorage.__tablename__,
                    'sender_or_recipient': SENDER,
                    'type': TransferFilterEnum.DISCRETE,
                    'values': ao.existing_options
                }
            if ao.filter_visibility in [MetricsVisibility.SENDER_AND_RECIPIENT, MetricsVisibility.RECIPIENT]:
                filters[ao.name + ',recipient'] = {
                    'name': 'Recipient ' + ao.name.capitalize(),
                    'table': CustomAttributeUserStorage.__tablename__,
                    'sender_or_recipient': RECIPIENT,
                    'type': TransferFilterEnum.DISCRETE,
                    'values': ao.existing_options
                }
        else:
            filters[ao.name] = {
                'name': ao.name.capitalize(),
                'table': CustomAttributeUserStorage.__tablename__,
                'type': TransferFilterEnum.DISCRETE,
                'values': ao.existing_options
            }
    return filters

class Filters(object):
    @property
    def transfer_filters(self):
        return {
            'rounded_transfer_amount': {
                'name': 'Transfer Amount',
                'table': CreditTransfer.__tablename__,
                'type': TransferFilterEnum.INT_RANGE
            },
            'public_transfer_type': {
                'name': "Transfer Type",
                'table': CreditTransfer.__tablename__,
                'type': TransferFilterEnum.DISCRETE,
                'values': ['PAYMENT', 'DEPOSIT', 'WITHDRAWAL', 'EXCHANGE', 'FEE', 'DISBURSEMENT', 'RECLAMATION', 'AGENT_IN', 'AGENT_OUT', 'INCENTIVE']
            },
        }

    @property
    def user_filters(self):
        return {
            'created': {
                'name': "Created",
                'table': User.__tablename__,
                'type' : TransferFilterEnum.DATE_RANGE,
            },
            'user_type': {
                'name': "Participant Type",
                'table': User.__tablename__,
                'type': TransferFilterEnum.BOOLEAN_MAPPING,
                'values': [BENEFICIARY, VENDOR, TOKEN_AGENT, GROUP_ACCOUNT]
            },
            '_location': {
                'name': "Location",
                'table': User.__tablename__,
                'type': TransferFilterEnum.DISCRETE,
                'values' : [u._location for u in db.session.query(User._location).distinct()]
            },
            'rounded_account_balance': {
                'name': "Balance",
                'table': TransferAccount.__tablename__,
                'type' : TransferFilterEnum.INT_RANGE
            },
        }

    @property
    def tx_rx_user_filters(self):
        return {
            'created,sender': {
                'name': "Sender Created",
                'table': User.__tablename__,
                'sender_or_recipient': SENDER,
                'type' : TransferFilterEnum.DATE_RANGE,
            },
            'user_type,sender': {
                'name': "Sender Participant Type",
                'table': User.__tablename__,
                'sender_or_recipient': SENDER,
                'type': TransferFilterEnum.BOOLEAN_MAPPING,
                'values': [BENEFICIARY, VENDOR, TOKEN_AGENT, GROUP_ACCOUNT]
            },
            '_location,sender': {
                'name': "Sender Location",
                'table': User.__tablename__,
                'sender_or_recipient': SENDER,
                'type': TransferFilterEnum.DISCRETE,
                'values' : [u._location for u in db.session.query(User._location).distinct()]
            },
            'rounded_account_balance,sender': {
                'name': "Sender Balance",
                'table': TransferAccount.__tablename__,
                'sender_or_recipient': SENDER,
                'type' : TransferFilterEnum.INT_RANGE
            },
            'created,recipient': {
                'name': "Recipient Created",
                'table': User.__tablename__,
                'sender_or_recipient': RECIPIENT,
                'type' : TransferFilterEnum.DATE_RANGE,
            },
            'user_type,recipient': {
                'name': "Recipient Participant Type",
                'table': User.__tablename__,
                'sender_or_recipient': RECIPIENT,
                'type': TransferFilterEnum.BOOLEAN_MAPPING,
                'values': [BENEFICIARY, VENDOR, TOKEN_AGENT, GROUP_ACCOUNT]
            },
            '_location,recipient': {
                'name': "Recipient Location",
                'table': User.__tablename__,
                'sender_or_recipient': RECIPIENT,
                'type': TransferFilterEnum.DISCRETE,
                'values' : [u._location for u in db.session.query(User._location).distinct()]
            },
            'rounded_account_balance,recipient': {
                'name': "Recipient Balance",
                'table': TransferAccount.__tablename__,
                'sender_or_recipient': RECIPIENT,
                'type' : TransferFilterEnum.INT_RANGE
            },
        }

    @property
    def ALL_FILTERS(self):
        return {
            **get_custom_attribute_filters(distinct_sender_and_recipient=True),
            **get_custom_attribute_filters(distinct_sender_and_recipient=False),
            **self.transfer_filters,
            **self.user_filters,
            **self.tx_rx_user_filters,
        }

    @property
    def TRANSFER_FILTERS(self): return { **self.tx_rx_user_filters, **self.transfer_filters, **get_custom_attribute_filters(distinct_sender_and_recipient=True) }
    
    @property
    def USER_FILTERS(self): 
        return { **self.user_filters, **get_custom_attribute_filters(distinct_sender_and_recipient=False) }

# will return a dictionary with table names as keys
# values will be a dictionary of array of tuples
# values on the outer array should be AND'd together
def process_transfer_filters(encoded_filters):
    # parse and prepare filters for calculating transfer stats
    if (encoded_filters is None):
        return
    filters = Filters()

    filter_list = parse_filter_string(encoded_filters)

    filter_dict = {}

    for f in filter_list:

        unprocessed_attribute = f['attribute']
        table = filters.ALL_FILTERS[unprocessed_attribute]['table']
        sender_or_recipient = filters.ALL_FILTERS[unprocessed_attribute]['sender_or_recipient'] if 'sender_or_recipient' in filters.ALL_FILTERS[unprocessed_attribute] else False

        processed = handle_filter(**f)
        if (table, sender_or_recipient) not in filter_dict:
            filter_dict[(table, sender_or_recipient)] = []
        filter_dict[(table, sender_or_recipient)].append(processed)

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
    filters = Filters()
    attribute_type = filters.ALL_FILTERS[attribute]['type']
    if attribute_type == TransferFilterEnum.BOOLEAN_MAPPING:
        return handle_boolean_mapping(attribute, comparator, value)

    elif attribute_type == TransferFilterEnum.DISCRETE:
        return handle_discrete(attribute, comparator, value)
    else:
        return handle_other_types(attribute, comparator, value, attribute_type)


def handle_boolean_mapping(attribute, comparator, value):

    filters = []
    for v in value:
        attribute = BOOLEAN_MAPPINGS[v]
        filters.append((attribute, "EQ", True))

    return filters


def handle_discrete(attribute, comparator, value):
    return [(attribute, "EQ", value)]


def handle_other_types(attribute, comparator, value, attribute_type):
    value = value if attribute_type == TransferFilterEnum.DATE_RANGE else float(value)
    return [(attribute, comparator, value)]
