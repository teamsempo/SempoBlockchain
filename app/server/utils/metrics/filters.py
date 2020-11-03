# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccount
from server.utils.metrics import metrics_cache
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage

from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum, TransferStatusEnum
from flask import g
from server.models.user import User
from sqlalchemy.sql import func, text
from sqlalchemy import case, or_
from server import db, red, bt

def apply_filters(query, filters, query_table):
    """
    Applies a dictionary of filters to a query.
    If the table being queried is the CreditTransfer, will add a join on the sender user and sender transfer accounts
    (via _determine_join_conditions) so that we can filter on attributes like the sender balance or sender name

    Filter Dictionary format is:
    Key: the table name, eg 'transfer_account'
    Value: list of Filter Rules applying to that table.


    {'transfer_account': [[('rounded_account_balance', 'GT', 100.0)]]}

    :param query: The base query
    :param filters: A filter dictionary
    :param query_table: The table object that we're querying against
    :return:
    """

    if filters is None:
        return query

    for filter_table_name, _filts in filters.items():
        filter_table, _, sender_or_recipient = filter_table_name.partition(',')
        user_join_attribute, account_join_attribute = _determine_join_conditions(query_table, sender_or_recipient)
        if filter_table == TransferAccount.__tablename__:
                # only join transfer account if table is not transfer account
                if query_table.__tablename__ == filter_table: 
                    query = _apply_single_column_filter(query, _filts, TransferAccount, None, None) 
                else:
                    query = _apply_single_column_filter(query, _filts, TransferAccount, account_join_attribute, None)

        elif filter_table == User.__tablename__:
                # only join user account if table is not user 
                if query_table.__tablename__ == filter_table:
                    query = _apply_single_column_filter(query, _filts, User, None, None)
                else:
                    query = _apply_single_column_filter(query, _filts, User, None, user_join_attribute)

        elif filter_table == CreditTransfer.__tablename__:
                # No join needed for CreditTransfer, since it's only availible to be filtered on when directly queried 
                query = _apply_single_column_filter(query, _filts, CreditTransfer, None, None, None)
        elif filter_table == CustomAttributeUserStorage.__tablename__ and user_join_attribute is not None:
            query = _apply_ca_filters(query, _filts, user_join_attribute)
    return query

def _determine_join_conditions(query_table, sender_or_recipient):
    if query_table == CreditTransfer:
        if sender_or_recipient == 'recipient':
            return CreditTransfer.recipient_user_id, CreditTransfer.recipient_transfer_account_id
        else:
            return CreditTransfer.sender_user_id, CreditTransfer.sender_transfer_account_id
    if query_table == User:
        return User.id, None

def _apply_single_column_filter(query, filters, target_table, account_join_attribute=None, user_join_attribute=None, transfer_join_attribute=None):
    """
    Converts a list of filter rule tuples (applying to a particular table specified
    by target_table) to an actual alchemy query and applies it
    :param query: the base query
    :param filters: the list of filter rule tuples
    :param target_table: the table being filtered on
    :return:
    """
    joined_tables = [mapper.class_ for mapper in query._join_entities]
    if target_table not in joined_tables:
        if target_table.__tablename__ == TransferAccount.__tablename__ and account_join_attribute is not None:
            if TransferAccount not in joined_tables:
                query = query.join(TransferAccount, TransferAccount.id == account_join_attribute)
        elif target_table.__tablename__ == User.__tablename__ and user_join_attribute is not None:
                query = query.join(User, User.id == user_join_attribute)

    for batches in filters:
        to_batch = []
        for _filt in batches:
            column = _filt[0].split(',')[0]
            comparator = _filt[1]
            val = _filt[2]

            if comparator == 'EQ':
                val = val if isinstance(val, list) else [val]
                to_batch.append(getattr(target_table, column).in_(val))
            elif comparator == 'GT':
                to_batch.append(getattr(target_table, column) > val)
            elif comparator == "LT":
                to_batch.append(getattr(target_table, column) < val)
        query = query.filter(or_(*to_batch))
    return query

def _apply_ca_filters(query, filters, user_join_condition):

    # get all custom attributes and create pivot table
    new_cs = [CustomAttributeUserStorage.user_id]
    for value in db.session.query(CustomAttributeUserStorage.name).distinct():
        value = value[0]
        new_cs.append(
             func.max(case(
                [(CustomAttributeUserStorage.name == value, CustomAttributeUserStorage.value)],
                else_=None
            )).label(value)
        )

    # join pivot table of custom attributes
    pivot = db.session.query(*new_cs).group_by(CustomAttributeUserStorage.user_id).subquery()
    query = query.outerjoin(pivot, user_join_condition == pivot.c.user_id)
    
    for batches in filters:
        to_batch = []
        for _filt in batches:
            column = _filt[0].split(',')[0]
            comparator = _filt[1]
            val = _filt[2]

            if comparator == 'EQ':
                val = val if isinstance(val, list) else [val]
                val = [f'\"{element}\"' for element in val] # needs ot be in form '"{item}"' for json string match
                to_batch.append(pivot.c[column].in_(val))
            elif comparator == 'GT':
               to_batch.append(pivot.c[column] > val)
            elif comparator == "LT":
                to_batch.append(pivot.c[column] < val)
        query = query.filter(or_(*to_batch))

    return query


disbursement_filters = [
    CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
    CreditTransfer.transfer_type == TransferTypeEnum.PAYMENT,
    CreditTransfer.transfer_subtype == TransferSubTypeEnum.DISBURSEMENT
]

reclamation_filters = [
    CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
    CreditTransfer.transfer_type == TransferTypeEnum.PAYMENT,
    CreditTransfer.transfer_subtype == TransferSubTypeEnum.RECLAMATION
]

withdrawal_filters = [
    CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
    CreditTransfer.transfer_type == TransferTypeEnum.WITHDRAWAL
]


transaction_volume_filters = [
    CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
]

standard_payment_filters = [
    CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
    CreditTransfer.transfer_type == TransferTypeEnum.PAYMENT,
    CreditTransfer.transfer_subtype == TransferSubTypeEnum.STANDARD
]

exchanged_filters = [
    CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
    CreditTransfer.transfer_type == TransferTypeEnum.EXCHANGE,
]

beneficiary_filters = [User.has_beneficiary_role == True]
vendor_filters = [User.has_vendor_role == True]

exhaused_balance_filters = [
    CreditTransfer.transfer_type == TransferTypeEnum.PAYMENT,
    TransferAccount._balance_wei == 0
]

