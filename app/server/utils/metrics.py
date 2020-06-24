
from server import db, red, bt

from flask import g

from server.models.transfer_usage import TransferUsage
from server.models.transfer_account import TransferAccount
from server.models.blockchain_address import BlockchainAddress
from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage

from server.utils import metrics_cache
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum, TransferStatusEnum
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql import func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import case, or_
import sqlalchemy
import datetime, json

def calculate_transfer_stats(total_time_series=False, start_date=None, end_date=None,
                             user_filter={}):
    print('METRIC STUFF')
    date_filter = []
    filter_active = False
    if start_date is not None and end_date is not None:
        date_filter.append(CreditTransfer.created >= start_date)
        date_filter.append(CreditTransfer.created <= end_date)
        filter_active = True

    disbursement_filters = [
        CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
        CreditTransfer.transfer_type == TransferTypeEnum.PAYMENT,
        CreditTransfer.transfer_subtype == TransferSubTypeEnum.DISBURSEMENT]

    standard_payment_filters = [
        CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
        CreditTransfer.transfer_type == TransferTypeEnum.PAYMENT,
        CreditTransfer.transfer_subtype == TransferSubTypeEnum.STANDARD
    ]

    exchanged_filters = [
        CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE,
        CreditTransfer.transfer_type == TransferTypeEnum.EXCHANGE,
        CreditTransfer.token == g.active_organisation.token
    ]

    beneficiary_filters = [User.has_beneficiary_role == True]
    vendor_filters = [User.has_vendor_role == True]

    exhaused_balance_filters = [
        CreditTransfer.transfer_type == TransferTypeEnum.PAYMENT,
        TransferAccount._balance_wei == 0
    ]

    transfer_use_filters = [
        *standard_payment_filters,
        CreditTransfer.transfer_use.isnot(None),
    ]

    # Disable cache if any filters are being used
    disable_cache = False
    if user_filter or date_filter:
        disable_cache = True

    total_distributed = db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
    total_distributed = apply_filters(total_distributed, user_filter, CreditTransfer)
    total_distributed = total_distributed.filter(*disbursement_filters).filter(*date_filter)
    total_distributed = metrics_cache.execute_with_partial_history_cache('total_distributed', total_distributed, CreditTransfer, metrics_cache.SUM, disable_cache=disable_cache)

    total_spent = db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
    total_spent = apply_filters(total_spent, user_filter, CreditTransfer)
    total_spent = total_spent.filter(*standard_payment_filters).filter(*date_filter)
    total_spent = metrics_cache.execute_with_partial_history_cache('total_spent', total_spent, CreditTransfer, metrics_cache.SUM, disable_cache=disable_cache)

    total_exchanged = db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
    total_exchanged = apply_filters(total_exchanged, user_filter, CreditTransfer)
    total_exchanged = total_exchanged.filter(*exchanged_filters).filter(*date_filter)
    total_exchanged = metrics_cache.execute_with_partial_history_cache('total_exchanged', total_exchanged, CreditTransfer, metrics_cache.SUM, disable_cache=disable_cache)

    total_beneficiaries = db.session.query(User).filter(*beneficiary_filters)
    total_beneficiaries = metrics_cache.execute_with_partial_history_cache('total_beneficiaries', total_beneficiaries, CreditTransfer, metrics_cache.COUNT, disable_cache=disable_cache)

    total_vendors = db.session.query(User).filter(*vendor_filters)
    total_vendors = metrics_cache.execute_with_partial_history_cache('total_vendors', total_vendors, CreditTransfer, metrics_cache.COUNT, disable_cache=disable_cache)

    total_users = total_beneficiaries + total_vendors

    has_transferred_count = db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id))
        .label('transfer_count'))\
        .filter(*standard_payment_filters) \
        .filter(*date_filter) \
            .first().transfer_count

    exhausted_balance_count = db.session.query(func.count(func.distinct(
        CreditTransfer.sender_transfer_account_id))
        .label('transfer_count')) \
        .join(CreditTransfer.sender_transfer_account)\
        .filter(*exhaused_balance_filters) \
        .filter(*date_filter) \
            .first().transfer_count

    daily_transaction_volume = db.session.query(func.sum(CreditTransfer.transfer_amount).label('volume'),
                                                func.date_trunc('day', CreditTransfer.created).label('date'))
    daily_transaction_volume = apply_filters(daily_transaction_volume, user_filter,  CreditTransfer)
    daily_transaction_volume = daily_transaction_volume.group_by(func.date_trunc('day', CreditTransfer.created))\
        .filter(*standard_payment_filters) \
        .filter(*date_filter)
    daily_transaction_volume = metrics_cache.execute_with_partial_history_cache('daily_transaction_volume', daily_transaction_volume, CreditTransfer, metrics_cache.SUM_OBJECTS, disable_cache=disable_cache)

    daily_disbursement_volume = db.session.query(func.sum(CreditTransfer.transfer_amount).label('volume'),
                                                func.date_trunc('day', CreditTransfer.created).label('date'))
    daily_disbursement_volume = apply_filters(daily_disbursement_volume, user_filter, CreditTransfer)
    daily_disbursement_volume = daily_disbursement_volume.group_by(func.date_trunc('day', CreditTransfer.created)) \
        .filter(*disbursement_filters) \
        .filter(*date_filter)
    daily_disbursement_volume = metrics_cache.execute_with_partial_history_cache('daily_disbursement_volume', daily_disbursement_volume, CreditTransfer, metrics_cache.SUM_OBJECTS, disable_cache=disable_cache)

    transfer_use_breakdown = db.session.query(CreditTransfer.transfer_use.cast(JSONB),func.count(CreditTransfer.transfer_use))
    transfer_use_breakdown = apply_filters(transfer_use_breakdown, user_filter, CreditTransfer)
    transfer_use_breakdown = transfer_use_breakdown.filter(*transfer_use_filters) \
        .group_by(CreditTransfer.transfer_use.cast(JSONB)) \
            .all()

    try:
        last_day = daily_transaction_volume[0][1]
        last_day_volume = daily_transaction_volume[0][0]
        transaction_vol_list = [
            {'date': item[1].isoformat(), 'volume': item[0]} for item in daily_transaction_volume
        ]
    except IndexError:  # No transactions
        last_day = datetime.datetime.utcnow()
        last_day_volume = 0
        has_transferred_count = 0
        transaction_vol_list = [{'date': datetime.datetime.utcnow().isoformat(), 'volume': 0}]

    try:
        disbursement_vol_list = [
            {'date': item[1].isoformat(), 'volume': item[0]} for item in daily_disbursement_volume
        ]
    except IndexError:
        disbursement_vol_list = [{'date': datetime.datetime.utcnow().isoformat(), 'volume': 0}]

    try:
        master_wallet_balance = cached_funds_available() # SINGLE ORG (rest is multi-org base)
    except:
        master_wallet_balance = 0

    data = {
        'total_distributed': total_distributed,
        'total_spent': total_spent,
        'total_exchanged': total_exchanged,
        'has_transferred_count': has_transferred_count,
        'zero_balance_count': exhausted_balance_count,
        'total_beneficiaries': total_beneficiaries,
        'total_users': total_users,
        'master_wallet_balance': master_wallet_balance,
        'daily_transaction_volume': transaction_vol_list,
        'daily_disbursement_volume': disbursement_vol_list,
        'transfer_use_breakdown': transfer_use_breakdown,
        'last_day_volume': {'date': last_day.isoformat(), 'volume': last_day_volume},
        'filter_active': filter_active
    }
    print('METRIC STUFF===')

    return data

def apply_filters(query, filters, query_table):

    if filters is None:
        return query

    user_join_attribute, account_join_attribute = determine_join_conditions(query_table)

    for filter_table_name, _filts in filters.items():
        if filter_table_name == TransferAccount.__tablename__:
                # only join transfer account if table is not transfer account
                if query_table.__tablename__ == filter_table_name: 
                    query = apply_single_column_filter(query, _filts, TransferAccount, None, None) 
                else:
                    query = apply_single_column_filter(query, _filts, TransferAccount, account_join_attribute, None)

        elif filter_table_name == User.__tablename__:
                # only join user account if table is not user 
                if query_table.__tablename__ == filter_table_name:
                    query = apply_single_column_filter(query, _filts, User, None, None)
                else:
                    query = apply_single_column_filter(query, _filts, User, None, user_join_attribute)

        elif filter_table_name == CustomAttributeUserStorage.__tablename__ and user_join_attribute is not None:
            query = apply_ca_filters(query, _filts, user_join_attribute)
    return query

def determine_join_conditions(table):
    if table == CreditTransfer:
        return CreditTransfer.sender_user_id, CreditTransfer.sender_transfer_account_id
    if table == User:
        return User.id, None

def apply_ca_filters(query, filters, user_join_condition):

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
            column = _filt[0]
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

def apply_single_column_filter(query, filters, target_table, account_join_attribute=None, user_join_attribute=None):


    if target_table.__tablename__ == TransferAccount.__tablename__ and account_join_attribute is not None:
        query = query.join(TransferAccount, TransferAccount.id == account_join_attribute)
    elif target_table.__tablename__ == User.__tablename__ and user_join_attribute is not None:
        query = query.join(User, User.id == user_join_attribute)

    for batches in filters:
        to_batch = []
        for _filt in batches:
            column = _filt[0]
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

def cached_funds_available(allowed_cache_age_seconds=60):
    """
    IF refreshing cash THEN:
        return: [current blockchain balance] - [all transfers with blockchain state pending or unknown]
        save to cache: [funds available], [ID of highest transfer used in cache], [cache creation datetime]
    ELSE
        return: [funds available at last cache] - [all non-failed transfers since last cache]
    Max Txn ID is a simple way to determine whether txn was used in cache or not, and thus needs to be accounted for
    :param allowed_cache_age_seconds: how long between checking the blockchain for external funds added or removed
    :return: amount of funds available
    """
    token = g.active_organisation.org_level_transfer_account.token

    balance_wei = bt.get_wallet_balance(
        g.active_organisation.org_level_transfer_account.blockchain_address,
        token
    )

    return token.token_amount_to_system(balance_wei)

    refresh_cache = False
    funds_available_cache = red.get('funds_available_cache')

    try:
        parsed_cache = json.loads(funds_available_cache)

        last_updated_datetime = datetime.datetime.fromtimestamp(float(parsed_cache['last_updated']))

        earliest_allowed = datetime.datetime.utcnow() - datetime.timedelta(seconds=allowed_cache_age_seconds)
        if last_updated_datetime < earliest_allowed:
            refresh_cache = True

    except Exception as e:
        refresh_cache = True


    if refresh_cache:

        master_wallet_balance = get_wallet_balance()

        highest_transfer_id_checked = 0
        required_blockchain_statuses = ['PENDING', 'UNKNOWN']

    else:
        cached_funds_available = parsed_cache['cached_funds_available']
        highest_transfer_id_checked = parsed_cache['highest_transfer_id_checked']
        required_blockchain_statuses = ['PENDING', 'UNKNOWN', 'COMPLETE']



    new_dibursements     = (CreditTransfer.query
                            .filter(CreditTransfer.transfer_type == TransferTypeEnum.PAYMENT)
                            .filter(CreditTransfer.transfer_subtype == TransferSubTypeEnum.DISBURSEMENT)
                            .filter(CreditTransfer.transfer_status == TransferStatusEnum.COMPLETE)
                            .filter(CreditTransfer.id > highest_transfer_id_checked)
                            .filter(CreditTransfer.created >
                                    datetime.datetime.utcnow() - datetime.timedelta(hours=36))
                            .all())


    local_disbursement_value = 0
    for disbursement in new_dibursements:

        status = disbursement.blockchain_status

        if status in required_blockchain_statuses:
            local_disbursement_value += disbursement.transfer_amount

    if refresh_cache:

        balance = master_wallet_balance - local_disbursement_value

        if len(new_dibursements) > 0:
            highest_transfer_id_checked = new_dibursements[-1].id
        else:
            all_transfers = CreditTransfer.query.all()
            if len(all_transfers) > 0:
                highest_transfer_id_checked = all_transfers[-1].id
            else:
                highest_transfer_id_checked = 0

        cache_data = {
            'cached_funds_available': balance,
            'highest_transfer_id_checked': highest_transfer_id_checked,
            'last_updated': datetime.datetime.utcnow().timestamp()
        }

        red.set('funds_available_cache', json.dumps(cache_data))

        balance = master_wallet_balance - local_disbursement_value

        return balance

    else:

        balance = cached_funds_available - local_disbursement_value

        return balance