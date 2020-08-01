# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

from sqlalchemy.sql import func

from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccount
from server.models.user import User
from server.utils.metrics import filters, metrics_cache, metric, process_timeseries, metric_group, group
from server.utils.metrics.metrics_const import *

from server import db, red, bt
from sqlalchemy.dialects.postgresql import JSONB

class TransferStats(metric_group.MetricGroup):
    def __init__(self, group_strategy, timeseries_unit = 'day'):
        self.filterable_attributes = [DATE, CUSTOM_ATTRIBUTE, TRANSFER_ACCOUNT, CREDIT_TRANSFER, USER]
        self.timeseries_unit = timeseries_unit
        self.metrics = []

        total_distributed_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
        self.metrics.append(metric.Metric(
            metric_name='total_distributed',
            query=total_distributed_query,
            object_model=CreditTransfer,
            stock_filters=[filters.disbursement_filters],
            caching_combinatory_strategy=metrics_cache.SUM,
            filterable_by=self.filterable_attributes,
            bypass_user_filters=True
        ))

        total_spent_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
        self.metrics.append(metric.Metric(
            metric_name='total_spent',
            query=total_spent_query,
            object_model=CreditTransfer,
            stock_filters=[filters.standard_payment_filters],
            caching_combinatory_strategy=metrics_cache.SUM,
            filterable_by=self.filterable_attributes))

        total_exchanged_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
        self.metrics.append(metric.Metric(
            metric_name='total_exchanged',
            query=total_exchanged_query,
            object_model=CreditTransfer,
            stock_filters=[filters.exchanged_filters],
            caching_combinatory_strategy=metrics_cache.SUM,
            filterable_by=self.filterable_attributes))

        exhausted_balance_count_query = db.session.query(func.count(func.distinct(
            CreditTransfer.sender_transfer_account_id))
                .label('count')) \
                .join(CreditTransfer.sender_transfer_account)
        self.metrics.append(metric.Metric(
            metric_name='exhausted_balance',
            query=exhausted_balance_count_query,
            object_model=CreditTransfer,
            stock_filters=[filters.exhaused_balance_filters],
            caching_combinatory_strategy=metrics_cache.FIRST_COUNT,
            filterable_by=self.filterable_attributes,
            bypass_user_filters=True))

        has_transferred_count_query = db.session.query(func.count(func.distinct(
            CreditTransfer.sender_user_id))
            .label('count'))
        self.metrics.append(metric.Metric(
            metric_name='has_transferred_count',
            query=has_transferred_count_query,
            object_model=CreditTransfer,
            stock_filters=[filters.standard_payment_filters],
            caching_combinatory_strategy=metrics_cache.FIRST_COUNT,
            filterable_by=self.filterable_attributes,
            bypass_user_filters=True))

        # Timeseries Metrics
        transaction_volume_timeseries_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('volume'),
                func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date'), group_strategy.group_by_column).group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created))
        aggregated_transaction_volume_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('volume'), group_strategy.group_by_column)
        total_transaction_volume_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('volume'))
        self.metrics.append(metric.Metric(
            metric_name='daily_disbursement_volume',
            is_timeseries=True,
            query=group_strategy.build_query_group_by_with_join(transaction_volume_timeseries_query, CreditTransfer),
            aggregated_query=group_strategy.build_query_group_by_with_join(aggregated_transaction_volume_query, CreditTransfer),
            total_query=total_transaction_volume_query,
            object_model=CreditTransfer,
            stock_filters=[filters.disbursement_filters],
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes,
            query_actions=[FORMAT_TIMESERIES],
            aggregated_query_actions=[FORMAT_AGGREGATE_METRICS],
            total_query_actions=[GET_FIRST],
        ))

        self.metrics.append(metric.Metric(
            metric_name='daily_transaction_volume',
            is_timeseries=True,
            query=group_strategy.build_query_group_by_with_join(transaction_volume_timeseries_query, CreditTransfer),
            aggregated_query=group_strategy.build_query_group_by_with_join(aggregated_transaction_volume_query, CreditTransfer),
            total_query=total_transaction_volume_query,
            object_model=CreditTransfer,
            stock_filters=[filters.standard_payment_filters],
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes,
            query_actions=[FORMAT_TIMESERIES],
            aggregated_query_actions=[FORMAT_AGGREGATE_METRICS],
            total_query_actions=[GET_FIRST],
        ))

        self.metrics.append(metric.Metric(
            metric_name='all_payments_volume',
            is_timeseries=True,
            query=group_strategy.build_query_group_by_with_join(transaction_volume_timeseries_query, CreditTransfer),
            aggregated_query=group_strategy.build_query_group_by_with_join(aggregated_transaction_volume_query, CreditTransfer),
            total_query=total_transaction_volume_query,
            object_model=CreditTransfer,
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes,
            query_actions=[FORMAT_TIMESERIES],
            aggregated_query_actions=[FORMAT_AGGREGATE_METRICS],
            total_query_actions=[GET_FIRST],
        ))

        self.metrics.append(metric.Metric(
            metric_name='transfer_amount_per_user',
            is_timeseries=True,
            query=group_strategy.build_query_group_by_with_join(transaction_volume_timeseries_query, CreditTransfer),
            aggregated_query=group_strategy.build_query_group_by_with_join(aggregated_transaction_volume_query, CreditTransfer),
            total_query=total_transaction_volume_query,
            object_model=CreditTransfer,
            stock_filters=[filters.standard_payment_filters],
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes,
            query_actions=[CALCULATE_TIMESERIES_PER_USER, FORMAT_TIMESERIES], # Add per user
            aggregated_query_actions=[CALCULATE_AGGREGATE_PER_USER, FORMAT_AGGREGATE_METRICS],
            total_query_actions=[GET_FIRST, CALCULATE_TOTAL_PER_USER],
        ))

        transaction_count_timeseries_query = db.session.query(func.count(CreditTransfer.id).label('volume'),
                func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date'), group_strategy.group_by_column).group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created))
        aggregated_transaction_count_query = db.session.query(func.count(CreditTransfer.id).label('volume'), group_strategy.group_by_column)
        total_transaction_count_query = db.session.query(func.count(CreditTransfer.id).label('volume'))
        self.metrics.append(metric.Metric(
            metric_name='daily_transaction_count',
            is_timeseries=True,
            query=group_strategy.build_query_group_by_with_join(transaction_count_timeseries_query, CreditTransfer),
            aggregated_query=group_strategy.build_query_group_by_with_join(aggregated_transaction_count_query, CreditTransfer),
            total_query=total_transaction_count_query,
            object_model=CreditTransfer,
            stock_filters=[filters.standard_payment_filters],
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes,
            query_actions=[FORMAT_TIMESERIES],
            aggregated_query_actions=[FORMAT_AGGREGATE_METRICS],
            total_query_actions=[GET_FIRST],
        ))
        
        self.metrics.append(metric.Metric(
            metric_name='trades_per_user',
            is_timeseries=True,
            query=group_strategy.build_query_group_by_with_join(transaction_count_timeseries_query, CreditTransfer),
            aggregated_query=group_strategy.build_query_group_by_with_join(aggregated_transaction_count_query, CreditTransfer),
            total_query=total_transaction_count_query,
            object_model=CreditTransfer,
            stock_filters=[filters.standard_payment_filters],
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes,
            query_actions=[CALCULATE_TIMESERIES_PER_USER, FORMAT_TIMESERIES], # Add per user
            aggregated_query_actions=[CALCULATE_AGGREGATE_PER_USER, FORMAT_AGGREGATE_METRICS],
            total_query_actions=[GET_FIRST, CALCULATE_TOTAL_PER_USER],
        ))

        active_users_timeseries_query = db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id)).label('volume'),
                func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date'), group_strategy.group_by_column).group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created))
        aggregated_active_users_query = db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id)).label('volume'), group_strategy.group_by_column)
        total_transaction_volume_query = db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id)).label('volume'))
        self.metrics.append(metric.Metric(
            metric_name='users_who_made_purchase',
            is_timeseries=True,
            query=group_strategy.build_query_group_by_with_join(active_users_timeseries_query, CreditTransfer),
            aggregated_query=group_strategy.build_query_group_by_with_join(aggregated_active_users_query, CreditTransfer),
            total_query=total_transaction_volume_query,
            object_model=CreditTransfer,
            #stock_filters=[filters.beneficiary_filters], # NOTE: Do we want this filter?
            stock_filters=[],
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes,
            query_actions=[FORMAT_TIMESERIES],
            aggregated_query_actions=[FORMAT_AGGREGATE_METRICS],
            total_query_actions=[GET_FIRST],
        ))
