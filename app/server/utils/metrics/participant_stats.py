from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from server import db

from server.models.credit_transfer import CreditTransfer
from server.models.user import User
from server.utils.metrics import metrics_cache, metric, metric_group
from server.utils.metrics.metrics_const import *


class ParticipantStats(metric_group.MetricGroup):
    def __init__(self, group_strategy, timeseries_unit = 'day', date_filter_attributes = None):
        self.filterable_attributes = [DATE, CUSTOM_ATTRIBUTE, TRANSFER_ACCOUNT, USER]
        self.timeseries_unit = timeseries_unit
        self.date_filter_attributes = date_filter_attributes
        self.metrics = []

        # Timeseries Metrics
        if group_strategy:
            users_created_timeseries_query = group_strategy.build_query_group_by_with_join(db.session.query(func.count(User.id).label('volume'),
                    func.date_trunc(self.timeseries_unit, self.date_filter_attributes[User]).label('date'), group_strategy.group_by_column)\
                    .group_by(func.date_trunc(self.timeseries_unit, self.date_filter_attributes[User])), User)
            aggregated_users_created_query = group_strategy\
                .build_query_group_by_with_join(db.session.query(func.count(User.id).label('volume'), group_strategy.group_by_column), User)
        else:
            users_created_timeseries_query = db.session.query(func.count(User.id).label('volume'),
                    func.date_trunc(self.timeseries_unit, self.date_filter_attributes[User]).label('date'))\
                    .group_by(func.date_trunc(self.timeseries_unit, self.date_filter_attributes[User]))
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
            timeseries_caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes,
            query_actions=[FORMAT_TIMESERIES],
            aggregated_query_actions=[FORMAT_AGGREGATE_METRICS],
            total_query_actions=[GET_FIRST],
        ))

        if group_strategy:
            active_users_timeseries_query = group_strategy.build_query_group_by_with_join(db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id)).label('volume'),
                    func.date_trunc(self.timeseries_unit, self.date_filter_attributes[CreditTransfer]).label('date'), group_strategy.group_by_column)\
                    .group_by(func.date_trunc(self.timeseries_unit, self.date_filter_attributes[CreditTransfer])), CreditTransfer)
            aggregated_active_users_query = group_strategy.build_query_group_by_with_join(db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id)).label('volume'), group_strategy.group_by_column), CreditTransfer)
        else:
            active_users_timeseries_query = db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id)).label('volume'),
                    func.date_trunc(self.timeseries_unit, self.date_filter_attributes[CreditTransfer]).label('date'))\
                    .group_by(func.date_trunc(self.timeseries_unit, self.date_filter_attributes[CreditTransfer]))
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
            timeseries_caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes,
            query_actions=[FORMAT_TIMESERIES],
            aggregated_query_actions=[FORMAT_AGGREGATE_METRICS],
            total_query_actions=[GET_FIRST],
        ))

        if group_strategy:
            total_users_timeseries_query = group_strategy.build_query_group_by_with_join(db.session.query(func.count(User.id).label('volume'),
                    func.date_trunc(self.timeseries_unit, self.date_filter_attributes[User]).label('date'), group_strategy.group_by_column)\
                    .group_by(func.date_trunc(self.timeseries_unit, self.date_filter_attributes[User])), User)

        else:
            total_users_timeseries_query = db.session.query(func.count(User.id).label('volume'),
                    func.date_trunc(self.timeseries_unit, self.date_filter_attributes[User]).label('date'))\
                    .group_by(func.date_trunc(self.timeseries_unit, self.date_filter_attributes[User]))
        self.metrics.append(metric.Metric(
            metric_name='total_population_cumulative',
            is_timeseries=True,
            query=total_users_timeseries_query,
            total_query=total_users_created_query,
            aggregated_query=aggregated_active_users_query,
            object_model=User,
            stock_filters=[],
            timeseries_caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes,
            aggregated_query_actions=[FORMAT_AGGREGATE_METRICS],
            total_query_actions=[GET_FIRST],
            query_actions=[ADD_MISSING_DAYS_TO_TODAY, ACCUMULATE_TIMESERIES, FORMAT_TIMESERIES]
        ))


