# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from server import db, red, bt

from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from server.utils.metrics import filters, metrics_cache, metric, metric_group
from server.utils.metrics.metrics_const import *


class ParticipantStats(metric_group.MetricGroup):
    def __init__(self, group_strategy, timeseries_unit = 'day'):
        self.filterable_attributes = [DATE, CUSTOM_ATTRIBUTE, TRANSFER_ACCOUNT, USER]
        self.timeseries_unit = timeseries_unit
        self.metrics = []

        total_beneficiaries_query = db.session.query(User)
        self.metrics.append(metric.Metric(
            metric_name='total_beneficiaries',
            query=total_beneficiaries_query,
            object_model=User,
            stock_filters=[filters.beneficiary_filters],
            caching_combinatory_strategy=metrics_cache.COUNT,
            filterable_by=self.filterable_attributes))

        total_vendors_query = db.session.query(User)
        self.metrics.append(metric.Metric(
            metric_name='total_vendors',
            query=total_vendors_query,
            object_model=User,
            stock_filters=[filters.vendor_filters],
            caching_combinatory_strategy=metrics_cache.COUNT,
            filterable_by=self.filterable_attributes))

        # Timeseries Metrics
        if group_strategy:
            users_created_timeseries_query = group_strategy.build_query_group_by_with_join(db.session.query(func.count(User.id).label('volume'),
                    func.date_trunc(self.timeseries_unit, User.created).label('date'), group_strategy.group_by_column).group_by(func.date_trunc(self.timeseries_unit, User.created)), User)
            aggregated_users_created_query = group_strategy.build_query_group_by_with_join(db.session.query(func.count(User.id).label('volume'), group_strategy.group_by_column), User)
        else:
            users_created_timeseries_query = db.session.query(func.count(User.id).label('volume'),
                    func.date_trunc(self.timeseries_unit, User.created).label('date')).group_by(func.date_trunc(self.timeseries_unit, User.created))
            aggregated_users_created_query = None
        total_users_created_query = db.session.query(func.count(User.id).label('volume'))
        self.metrics.append(metric.Metric(
            metric_name='users_created',
            is_timeseries=True,
            query=users_created_timeseries_query,
            aggregated_query=aggregated_users_created_query,
            total_query=total_users_created_query,
            object_model=User,
            #stock_filters=[filters.beneficiary_filters], # NOTE: Do we still want this filter?
            stock_filters=[],
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes,
            query_actions=[FORMAT_TIMESERIES],
            aggregated_query_actions=[FORMAT_AGGREGATE_METRICS],
            total_query_actions=[GET_FIRST],
        ))

        if group_strategy:
            active_users_timeseries_query = group_strategy.build_query_group_by_with_join(db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id)).label('volume'),
                    func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date'), group_strategy.group_by_column).group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created)), CreditTransfer)
            aggregated_active_users_query = group_strategy.build_query_group_by_with_join(db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id)).label('volume'), group_strategy.group_by_column), CreditTransfer)
        else:
            active_users_timeseries_query = db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id)).label('volume'),
                    func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date')).group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created))
            aggregated_active_users_query = None
        total_active_users_query = db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id)).label('volume'))
        self.metrics.append(metric.Metric(
            metric_name='active_users',
            is_timeseries=True,
            query=active_users_timeseries_query,
            aggregated_query=aggregated_active_users_query,
            total_query=total_active_users_query,
            object_model=CreditTransfer,
            #stock_filters=[filters.beneficiary_filters], # NOTE: Do we still want this filter?
            stock_filters=[],
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes,
            query_actions=[FORMAT_TIMESERIES],
            aggregated_query_actions=[FORMAT_AGGREGATE_METRICS],
            total_query_actions=[GET_FIRST],
        ))
