from sqlalchemy.sql import func

from server import db

from server.models.user import User
from server.utils.metrics import metrics_cache, metric, metric_group
from server.utils.metrics.metrics_const import *


class TotalUsers(metric_group.MetricGroup):
    def __init__(self, group_strategy, timeseries_unit = 'day', date_filter_attributes=None):
        self.filterable_attributes = [DATE, CUSTOM_ATTRIBUTE, TRANSFER_ACCOUNT, USER]
        self.timeseries_unit = timeseries_unit
        self.date_filter_attributes = date_filter_attributes
        self.metrics = []

        # Special case query-- this is just used to calculate grouped per_user
        if group_strategy:
            total_users_grouped_timeseries_query = db.session.query(func.count(User.id).label('volume'),
                    func.date_trunc(self.timeseries_unit, self.date_filter_attributes[User]).label('date'), group_strategy.group_by_column).group_by(func.date_trunc(self.timeseries_unit, self.date_filter_attributes[User]))
            self.total_users_grouped_timeseries = metric.Metric(
                metric_name='total_population_grouped',
                query=group_strategy.build_query_group_by_with_join(total_users_grouped_timeseries_query, User),
                object_model=User,
                stock_filters=[],
                query_caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
                filterable_by=self.filterable_attributes,
                query_actions=[ADD_MISSING_DAYS_TO_TODAY, ACCUMULATE_TIMESERIES])

        # Special case query-- this is just used to calculate ungrouped per_user
        total_users_timeseries_query = db.session.query(func.count(User.id).label('volume'),
                func.date_trunc(self.timeseries_unit, self.date_filter_attributes[User]).label('date')).group_by(func.date_trunc(self.timeseries_unit, self.date_filter_attributes[User]))
        self.total_users_timeseries = metric.Metric(
            metric_name='total_population',
            query=total_users_timeseries_query,
            object_model=User,
            stock_filters=[],
            query_caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
            filterable_by=self.filterable_attributes,
            query_actions=[ADD_MISSING_DAYS_TO_TODAY, ACCUMULATE_TIMESERIES])
