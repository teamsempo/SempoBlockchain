from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from server import db, red, bt

from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccount
from server.models.user import User
from server.utils.metrics import filters, metrics_cache, metric, process_timeseries
from server.utils.metrics.metrics_const import *

filterable_attributes = [DATE, CUSTOM_ATTRIBUTE, TRANSFER_ACCOUNT, USER]

total_beneficiaries_query = db.session.query(User)
total_beneficiaries = metric.Metric(
    metric_name='total_beneficiaries', 
    query=total_beneficiaries_query, 
    object_model=User, 
    stock_filters=[filters.beneficiary_filters], 
    caching_combinatory_strategy=metrics_cache.COUNT,
    filterable_by=filterable_attributes)

total_vendors_query = db.session.query(User)
total_vendors = metric.Metric(
    metric_name='total_vendors', 
    query=total_vendors_query, 
    object_model=User, 
    stock_filters=[filters.vendor_filters], 
    caching_combinatory_strategy=metrics_cache.COUNT,
    filterable_by=filterable_attributes)

daily_users_created_query = db.session.query(func.count(User.id).label('volume'),
        func.date_trunc('day', User.created).label('date')).group_by(func.date_trunc('day', User.created))
daily_users_created = metric.Metric(
    metric_name='daily_users_created', 
    query=daily_users_created_query, 
    object_model=User, 
    stock_filters=[], 
    caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
    filterable_by=filterable_attributes)

total_users_per_day_query = db.session.query(func.count(User.id).label('volume'),
        func.date_trunc('day', User.created).label('date')).group_by(func.date_trunc('day', User.created))
total_users_per_day = metric.Metric(
    metric_name='total_users_per_day', 
    query=total_users_per_day_query, 
    object_model=User, 
    stock_filters=[], 
    caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
    filterable_by=filterable_attributes)

total_users = metric.Metric(
    metric_name='total_users_per_day', 
    query=total_users_per_day_query, 
    object_model=User, 
    stock_filters=[ADD_MISSING_DAYS, ACCUMULATE_TIMESERIES], 
    caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
    filterable_by=filterable_attributes)

#process_timeseries


#total_users_per_day_query = db.session.query(func.count(User.id).label('volume'),
#        func.date_trunc('day', User.created).label('date')).group_by(func.date_trunc('day', User.created))
#print(total_users_per_day_query.all())
#print(total_users_per_day_query.all())
#print(total_users_per_day_query.all())
#print(total_users_per_day_query.all())
#print(total_users_per_day_query.all())
#
#user_query = db.session.query(func.count(User.id)).
#print(user_query.all())
#
