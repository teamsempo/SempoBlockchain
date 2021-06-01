from server.models.transfer_account import TransferAccount
from server.models.credit_transfer import CreditTransfer
from server.models.transfer_usage import TransferUsage
from server.models.user import User
from server.models.utils import credit_transfer_transfer_usage_association_table
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server.models.custom_attribute import CustomAttribute, MetricsVisibility
from server.utils.metrics.metrics_const import *
from server import db

# Every permutation of tables we want to join with, and how we would actually make that join
sender_group_joining_strategies = {
    CreditTransfer.__tablename__: {
        User.__tablename__: lambda query : query.join(User, User.id == CreditTransfer.sender_user_id),
        TransferAccount.__tablename__: lambda query : query.join(TransferAccount, TransferAccount.id == CreditTransfer.sender_transfer_account_id),
        CustomAttributeUserStorage.__tablename__: lambda query, name : query.join(User, CreditTransfer.sender_user_id == User.id)\
                                                                    .join(CustomAttributeUserStorage, User.id == CustomAttributeUserStorage.user_id)\
                                                                    .join(CustomAttribute, CustomAttribute.id == CustomAttributeUserStorage.custom_attribute_id)\
                                                                    .filter(CustomAttribute.name == name),
        TransferUsage.__tablename__: lambda query : query.join(credit_transfer_transfer_usage_association_table, 
                                    credit_transfer_transfer_usage_association_table.c.credit_transfer_id == CreditTransfer.id)\
                                    .join(TransferUsage, credit_transfer_transfer_usage_association_table.c.transfer_usage_id == TransferUsage.id)    
    },
    User.__tablename__: {
        CustomAttributeUserStorage.__tablename__: lambda query, name : query.join(CustomAttributeUserStorage, User.id == CustomAttributeUserStorage.user_id)\
                                                                    .join(CustomAttribute, CustomAttribute.id == CustomAttributeUserStorage.custom_attribute_id)\
                                                                    .filter(CustomAttribute.name == name),
        TransferAccount.__tablename__: lambda query : query.join(TransferAccount, TransferAccount.id == User.default_transfer_account_id),
    }
}

recipient_group_joining_strategies = {
    CreditTransfer.__tablename__: {
        User.__tablename__: lambda query : query.join(User, User.id == CreditTransfer.recipient_user_id),
        TransferAccount.__tablename__: lambda query : query.join(TransferAccount, TransferAccount.id == CreditTransfer.recipient_transfer_account_id),
        CustomAttributeUserStorage.__tablename__: lambda query, name : query.join(User, CreditTransfer.recipient_user_id == User.id)\
                                                                    .join(CustomAttributeUserStorage, User.id == CustomAttributeUserStorage.user_id)\
                                                                    .join(CustomAttribute, CustomAttribute.id == CustomAttributeUserStorage.custom_attribute_id)\
                                                                    .filter(CustomAttribute.name == name),
        TransferUsage.__tablename__: lambda query : query.join(credit_transfer_transfer_usage_association_table, 
                                    credit_transfer_transfer_usage_association_table.c.credit_transfer_id == CreditTransfer.id)\
                                    .join(TransferUsage, credit_transfer_transfer_usage_association_table.c.transfer_usage_id == TransferUsage.id)    
    },
    User.__tablename__: {
        CustomAttributeUserStorage.__tablename__: lambda query, name : query.join(CustomAttributeUserStorage, User.id == CustomAttributeUserStorage.user_id)\
                                                                    .join(CustomAttribute, CustomAttribute.id == CustomAttributeUserStorage.custom_attribute_id)\
                                                                    .filter(CustomAttribute.name == name),
        TransferAccount.__tablename__: lambda query : query.join(TransferAccount, TransferAccount.id == User.default_transfer_account_id),
    }
}

class Group(object):
    def build_query_group_by_with_join(self, query, query_object_model):
        """
        Figures out how to join the applicable tables to the base query, 
        then applies the group_by to the passed query
        :param query: the base query
        :param query_object_model: The base model being queried
        :return: The base query, with the applicable joins applied and group_by appended
        """
        grouped_query = query.group_by(self.group_by_column)
        if query_object_model.__tablename__ != self.group_object_model.__tablename__:
            try:
                if self.custom_attribute_field_name:
                    args = (grouped_query, self.custom_attribute_field_name)
                else:
                    args = (grouped_query,)
                if self.sender_or_recipient == 'recipient':
                    return recipient_group_joining_strategies[query_object_model.__tablename__][self.group_object_model.__tablename__](*args)
                else:
                    return sender_group_joining_strategies[query_object_model.__tablename__][self.group_object_model.__tablename__](*args)

            except KeyError:
                raise Exception(f'No strategy to join tables {query_object_model.__tablename__} and {self.group_object_model.__tablename__}')
        return grouped_query

    def get_api_representation(self):
        return {
            'name': self.name,
            'table': self.group_object_model.__tablename__,
            'sender_or_recipient': self.sender_or_recipient
        }

    def __init__(self,
                name,
                group_object_model,
                group_by_column,
                custom_attribute_field_name = None,
                sender_or_recipient = None):
        """
        :param name: The title of the group
        :param group_object_model: The object model of the thing we're grouping by
        :param group_by_column: The column object that we're grouping by
        """
        self.name = name
        self.group_object_model = group_object_model
        self.group_by_column = group_by_column
        self.custom_attribute_field_name = custom_attribute_field_name
        self.sender_or_recipient = sender_or_recipient

# Builds Group objects for all custom attributes in the database
def get_custom_attribute_groups():
    # Get all custom attributes and options
    attribute_options = db.session.query(CustomAttribute)\
        .filter(CustomAttribute.filter_visibility != MetricsVisibility.HIDDEN)
    # Build those into group objects
    groups = {}
    for ao in attribute_options:
        if ao.group_visibility == MetricsVisibility.SENDER or ao.group_visibility == MetricsVisibility.SENDER_AND_RECIPIENT:
            groups[ao.name+',sender'] = Group(ao.name.capitalize(), CustomAttributeUserStorage, CustomAttributeUserStorage.value, ao.name, sender_or_recipient='sender')
        if ao.group_visibility == MetricsVisibility.RECIPIENT or ao.group_visibility == MetricsVisibility.SENDER_AND_RECIPIENT:
            groups[ao.name+',recipient'] = Group(ao.name.capitalize(), CustomAttributeUserStorage, CustomAttributeUserStorage.value, ao.name, sender_or_recipient='recipient')
    return groups

class Groups(object):
    @property
    def GROUP_TYPES(self):
        fixed_groups = {
            UNGROUPED: None,
            TRANSFER_TYPE: Group('Transfer Type', CreditTransfer, CreditTransfer.public_transfer_type),
            TRANSFER_MODE: Group('Transfer Mode', CreditTransfer, CreditTransfer.transfer_mode),
            TRANSFER_STATUS: Group('Transfer Status', CreditTransfer, CreditTransfer.transfer_status),
            TRANSFER_USAGE: Group('Transfer Usages', TransferUsage, TransferUsage._name),
            SENDER_LOCATION: Group('Location', User, User._location, sender_or_recipient='sender'),
            SENDER_COOORDINATES: Group('Coordinates', User, User.coordinates, sender_or_recipient='sender'),
            SENDER_ACCOUNT_TYPE: Group('Account Type', TransferAccount, TransferAccount.account_type, sender_or_recipient='sender'),
            RECIPIENT_LOCATION: Group('Location', User, User._location, sender_or_recipient='recipient'),
            RECIPIENT_ACCOUNT_TYPE: Group('Account Type', TransferAccount, TransferAccount.account_type, sender_or_recipient='recipient'),
            RECIPIENT_COOORDINATES: Group('Coordinates', User, User.coordinates, sender_or_recipient='recipient'),

        }
        custom_attribute_groups = get_custom_attribute_groups()
        return {**fixed_groups, **custom_attribute_groups}

    # Transfers can handle ALL groups!
    @property
    def TRANSFER_GROUPS(self):
        return self.GROUP_TYPES

    # Users can only use ones with TransferAccount and CustomAttributeUserStorage
    @property
    def USER_GROUPS(self):
        fixed_groups = {
            SENDER_ACCOUNT_TYPE: self.GROUP_TYPES[SENDER_ACCOUNT_TYPE],
            RECIPIENT_ACCOUNT_TYPE: self.GROUP_TYPES[RECIPIENT_ACCOUNT_TYPE],
            SENDER_LOCATION: self.GROUP_TYPES[SENDER_LOCATION],
            RECIPIENT_LOCATION: self.GROUP_TYPES[RECIPIENT_LOCATION],
            SENDER_COOORDINATES: self.GROUP_TYPES[SENDER_COOORDINATES],
            RECIPIENT_COOORDINATES: self.GROUP_TYPES[RECIPIENT_COOORDINATES],
            UNGROUPED: None,
        }
        custom_attribute_groups = get_custom_attribute_groups()
        return {**fixed_groups, **custom_attribute_groups}
