from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from server import db, red, bt

from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccount
from server.models.user import User
from server.utils.metrics import filters, metrics_cache, metric, process_timeseries, metric_group
from server.utils.metrics.metrics_const import *


class ParticipantStats(metric_group.MetricGroup):
    def __init__(self, timeseries_unit = 'day'):
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

        users_created_timeseries_query = db.session.query(func.count(User.id).label('volume'),
                func.date_trunc(self.timeseries_unit, User.created).label('date')).group_by(func.date_trunc(self.timeseries_unit, User.created))
        self.metrics.append(metric.Metric(
            metric_name='users_created',  # Will rename when API breaking changes come in
            query=users_created_timeseries_query, 
            object_model=User, 
            stock_filters=[filters.beneficiary_filters], 
            caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
            filterable_by=self.filterable_attributes,
            timeseries_actions=[FORMAT_TIMESERIES, AGGREGATE_FORMATTED_TIMESERIES]))

        # Special case query-- this is just used to calculate per_user
        total_users_timeseries_query = db.session.query(func.count(User.id).label('volume'),
                func.date_trunc(self.timeseries_unit, User.created).label('date')).group_by(func.date_trunc(self.timeseries_unit, User.created))
        self.total_users_timeseries = metric.Metric(
            metric_name='total_population', 
            query=total_users_timeseries_query, 
            object_model=User, 
            stock_filters=[], 
            caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
            filterable_by=self.filterable_attributes,
            timeseries_actions=[ADD_MISSING_DAYS_TO_TODAY, ACCUMULATE_TIMESERIES])
