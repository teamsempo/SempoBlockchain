from server import db, red, bt

from flask import g

from server import executor
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum, TransferStatusEnum
from server.utils.metrics import metrics_const
from server.utils.metrics.transfer_stats import TransferStats
from server.utils.metrics.participant_stats import ParticipantStats
from server.utils.metrics.total_users import TotalUsers
from server.utils.metrics.group import Groups

from server.models.transfer_account import TransferAccount
from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server.models.organisation import Organisation
from server.models.token import Token

from sqlalchemy.sql import text
from sqlalchemy import text

import datetime, json
import pendulum

def calculate_transfer_stats(
    start_date=None,
    end_date=None,
    user_filter={},
    metric_type=metrics_const.ALL,
    requested_metric=metrics_const.ALL,
    disable_cache: bool = False,
    timeseries_unit = metrics_const.DAY,
    group_by = None,
    token_id = None):

    # Handle a situation where multi_org is used with orgs with different tokens
    # Also get the active token object so we can pass the currency name in the API
    tokens_to_orgs = {}
    mandatory_filter = {}
    organisations = [Organisation.query.get(o) for o in g.get('query_organisations', [])]
    tokens = [o.token for o in organisations]
    for o in organisations:
        token = o.token
        if token not in tokens_to_orgs:
            tokens_to_orgs[token] = []
        tokens_to_orgs[token].append(o)
    if len(tokens_to_orgs) > 1:
        if not token_id:
            token, orgs = next(iter(tokens_to_orgs.items()))
        else:
            token = Token.query.get(token_id)
            if token not in tokens_to_orgs:
                raise Exception(f'No active org with token {token.id}')
            orgs = tokens_to_orgs[token]
        g.query_organisations = [o.id for o in orgs]
        mandatory_filter = {
            'token_filter':{
                'current_setting': {'id': token.id, 'name': token.name},
                'options': [{'id': t.id, 'name':t.name} for t in tokens]
            }
        }
    if not organisations:
        org = g.active_organisation
        token = org.token
        timezone = org.timezone or 'UTC'

    tz = g.active_organisation.timezone or 'UTC'
    # Gets hours offset from UTC in timezone in hours
    time_offset = pendulum.from_timestamp(0, tz).offset/60/60

    date_filter_attributes = {
        CreditTransfer: CreditTransfer.created + text(f"interval '{time_offset} hours'"),
        User: User.created + text(f"interval '{time_offset} hours'"),
        TransferAccount: TransferAccount.created + text(f"interval '{time_offset} hours'")
    }

    # Disable cache if any filters are being used, or explicitly requested
    enable_cache = True
    if user_filter or start_date or end_date or disable_cache or timeseries_unit != metrics_const.DAY:
        enable_cache = False
    groups = Groups()
    group_strategy = groups.GROUP_TYPES[group_by]

    # We use total_users ungrouped if we are grouping OR filtering the population by a non-user-based attribute
    # We also only send the end_date of the date filters, since it needs to use all previous users through history to
    # aggregate current numbers correctly
    if group_strategy:
        groups_and_filters_tables = [group_strategy.group_object_model.__tablename__]
        for f in user_filter or []:
            groups_and_filters_tables.append(f)

    total_users = {}
    if group_strategy and set(groups_and_filters_tables).issubset(set([CustomAttributeUserStorage.__tablename__, User.__tablename__, TransferAccount.__tablename__])):
        total_users_stats = TotalUsers(group_strategy, timeseries_unit, date_filter_attributes=date_filter_attributes)
        total_users[metrics_const.GROUPED] = total_users_stats.total_users_grouped_timeseries.execute_query(user_filters=user_filter, date_filter_attributes=date_filter_attributes, enable_caching=enable_cache, end_date=end_date)
        total_users[metrics_const.UNGROUPED] = total_users_stats.total_users_timeseries.execute_query(user_filters=[], date_filter_attributes=date_filter_attributes, enable_caching=enable_cache, end_date=end_date)
    else:
        total_users_stats = TotalUsers(None, timeseries_unit, date_filter_attributes=date_filter_attributes)
        total_users[metrics_const.UNGROUPED] = total_users_stats.total_users_timeseries.execute_query(user_filters=[], date_filter_attributes=date_filter_attributes, enable_caching=enable_cache, end_date=end_date)

    # Determines which metrics the user is asking for, and calculate them
    if metric_type == metrics_const.TRANSFER:
        metrics_list = TransferStats(group_strategy, timeseries_unit, token, date_filter_attributes=date_filter_attributes).metrics
    elif metric_type == metrics_const.USER:
        metrics_list = ParticipantStats(group_strategy, timeseries_unit, date_filter_attributes=date_filter_attributes).metrics
    else:
        metrics_list = TransferStats(group_strategy, timeseries_unit, token, date_filter_attributes=date_filter_attributes).metrics + ParticipantStats(group_strategy, timeseries_unit, date_filter_attributes=date_filter_attributes).metrics
    
    # Ensure that the metric requested by the user is available
    availible_metrics = [m.metric_name for m in metrics_list]
    availible_metrics.append(metrics_const.ALL)
    if requested_metric not in availible_metrics:
        raise Exception(f'{requested_metric} is not an availible metric of type {metric_type}. Please choose one of the following: {", ".join(availible_metrics)}')

    def calculate_metric(metric):
        import threading
        with threading.Lock():
            db.session.flush()

            session = db.session
            print(session)
            print(f'Starting {threading.current_thread()}')

            dont_include_timeseries = True
            if requested_metric in [metric.metric_name, metrics_const.ALL]:
                dont_include_timeseries = False
            result = metric.execute_query(user_filters=user_filter, 
                                                        date_filter_attributes=date_filter_attributes, 
                                                        enable_caching=enable_cache, 
                                                        population_query_result=total_users, 
                                                        dont_include_timeseries=dont_include_timeseries, 
                                                        start_date=start_date, 
                                                        end_date=end_date,
                                                        group_by=group_by)
            print(type(result))
            db.session.flush()
        
            print(f'Ending {threading.current_thread()}')

            return metric.metric_name, result

    futures = []
    for metric in metrics_list:
        futures.append(executor.submit(calculate_metric, metric))
    data = {}
    for future in futures:
        metric_name, result = future.result()
        data[metric_name] = result

    data['mandatory_filter'] = mandatory_filter

    # Legacy and aggregate metrics which don't fit the modular pattern
    try:
        data['master_wallet_balance'] = g.active_organisation.org_level_transfer_account.balance
    except:
        data['master_wallet_balance'] = 0

    active_filters = []
    for uf in user_filter or []:
        for f in user_filter[uf]:
            active_filters.append(f[0][0])

    data['active_group_by'] = group_by
    data['active_filters'] = active_filters
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
