
from server import db, red, bt

from flask import g

from server.utils.metrics import filters, metrics_cache, metric, metrics_const
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum, TransferStatusEnum

from server.models.transfer_usage import TransferUsage
from server.models.transfer_account import TransferAccount
from server.models.blockchain_address import BlockchainAddress
from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage

from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql import func, text
from sqlalchemy.dialects.postgresql import JSONB
import sqlalchemy
import datetime, json

def calculate_transfer_stats(start_date=None, end_date=None, user_filter={}, metric_type=metrics_const.ALL, disable_cache = False):
    # TODO (next PR): Add token filter here!
    # - Check orgs being queried (dependant on multi-org PR)
    # - Create 'manditory filter' field which is returned in the response

    from server.utils.metrics import transfer_stats
    from server.utils.metrics import participant_stats

    date_filters = []
    if start_date is not None and end_date is not None:
        date_filters.append(CreditTransfer.created >= start_date)
        date_filters.append(CreditTransfer.created <= end_date)

    # Disable cache if any filters are being used, or explicitly requested
    enable_cache = True
    if user_filter or date_filters or disable_cache:
        enable_cache = False

    # Metrics taxonomy, used to determine which metrics to display when which 
    # metric_type is queried
    transfer_stats = [
        transfer_stats.total_distributed, 
        transfer_stats.total_spent, 
        transfer_stats.total_exchanged, 
        transfer_stats.exhausted_balance_count, 
        transfer_stats.has_transferred_count,
        transfer_stats.daily_transaction_volume, 
        transfer_stats.daily_disbursement_volume, 
        transfer_stats.transfer_use_breakdown
    ]

    participant_stats = [
        participant_stats.total_beneficiaries,
        participant_stats.total_vendors,
    ]
    all_stats = transfer_stats + participant_stats

    metric_sets_by_type = {
        metrics_const.ALL: all_stats,
        metrics_const.TRANSFER: transfer_stats,
        metrics_const.USER: participant_stats
    }

    data = {}
    for metric in metric_sets_by_type[metric_type]:
        data[metric.metric_name] = metric.execute_query(user_filters=user_filter, date_filters=date_filters, enable_caching=enable_cache)

    # Legacy and aggregate metrics which don't fit the modular pattern
    if metric_type in [metrics_const.ALL, metrics_const.USER]:
        data['total_users'] = data['total_vendors'] + data['total_beneficiaries']

    if metric_type in [metrics_const.ALL, metrics_const.TRANSFER]:
        try:
            last_day = data['daily_transaction_volume'][0][1]
            data['last_day_volume'] = data['daily_transaction_volume'][0][0]
            data['daily_transaction_volume'] = [
                {'date': item[1].isoformat(), 'volume': item[0]} for item in data['daily_transaction_volume']
            ]
        except IndexError:  # No transactions
            last_day = datetime.datetime.utcnow()
            last_day_volume = 0
            data['has_transferred_count'] = 0
            data['daily_transaction_volume'] = [{'date': datetime.datetime.utcnow().isoformat(), 'volume': 0}]
        
        data['last_day_volume']: {'date': last_day.isoformat(), 'volume': last_day_volume}

        try:
            data['daily_disbursement_volume'] = [
                {'date': item[1].isoformat(), 'volume': item[0]} for item in data['daily_disbursement_volume']
            ]
        except IndexError:
            data['daily_disbursement_volume'] = [{'date': datetime.datetime.utcnow().isoformat(), 'volume': 0}]

        try:
            data['master_wallet_balance'] = cached_funds_available()
        except:
            data['master_wallet_balance'] = 0

    return data


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

        master_wallet_balance = bt.get_wallet_balance()

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
