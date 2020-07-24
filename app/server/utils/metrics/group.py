# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

from server.models.transfer_account import TransferAccount
from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server.utils.metrics.metrics_const import *


# Every permutation of tables we want to join with, and how we would actually make that join
group_joining_strategies = {
    CreditTransfer.__tablename__: {
        User.__tablename__: lambda query : query.join(User, User.id == CreditTransfer.sender_user_id),
        TransferAccount.__tablename__: lambda query : query.join(TransferAccount, TransferAccount.id == CreditTransfer.sender_transfer_account_id),
        CustomAttributeUserStorage.__tablename__: lambda query : query.join(User, CreditTransfer.sender_user_id == User.id)\
                                                                    .join(CustomAttributeUserStorage, User.id == CustomAttributeUserStorage.user_id)\
                                                                    .filter(CustomAttributeUserStorage.name == 'gender')
    },
    User.__tablename__: {
        CustomAttributeUserStorage.__tablename__: lambda query : query.join(CustomAttributeUserStorage, User.id == CustomAttributeUserStorage.user_id)\
                                                                    .filter(CustomAttributeUserStorage.name == 'gender'),
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
                return group_joining_strategies[query_object_model.__tablename__][self.group_object_model.__tablename__](grouped_query)
            except KeyError:
                raise Exception(f'No strategy to join tables {query_object_model.__tablename__} and {self.group_object_model.__tablename__}')
        return grouped_query

    def get_api_representation(self):
        return {
            'name': self.name,
            'table': self.group_object_model.__tablename__,
        }

    def __init__(self,
                name,
                group_object_model,
                group_by_column):
        """
        :param name: The title of the group
        :param group_object_model: The object model of the thing we're grouping by
        :param group_by_column: The column object that we're grouping by
        """
        self.name = name
        self.group_object_model = group_object_model
        self.group_by_column = group_by_column


GROUP_TYPES = {
    GENDER: Group('Gender', CustomAttributeUserStorage, CustomAttributeUserStorage.value),
    TRANSFER_TYPE: Group('Transfer Type', CreditTransfer, CreditTransfer.transfer_type),
    TRANSFER_SUBTYPE: Group('Transfer Type', CreditTransfer, CreditTransfer.transfer_subtype),
    TRANSFER_STATUS: Group('Transfer Type', CreditTransfer, CreditTransfer.transfer_status),
    TRANSFER_MODE: Group('Transfer Type', CreditTransfer, CreditTransfer.transfer_mode),
    ACCOUNT_TYPE: Group('Account Type', TransferAccount, TransferAccount.account_type),
}

# Transfers can handle ALL groups!
TRANSFER_GROUPS = GROUP_TYPES

# Users can only use ones with TransferAccount and CustomAttributeUserStorage
USER_GROUPS = {
    GENDER: GROUP_TYPES[GENDER],
    ACCOUNT_TYPE: GROUP_TYPES[ACCOUNT_TYPE]
}