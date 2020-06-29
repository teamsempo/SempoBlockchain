from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccount
from server.models.user import User

from sqlalchemy.sql import func
from server.utils.metrics import filters, metrics_cache, metric
from server import db, red, bt
from sqlalchemy.dialects.postgresql import JSONB


total_beneficiaries_query = db.session.query(User)
total_beneficiaries = metric.Metric(
    metric_name='total_beneficiaries', 
    query=total_beneficiaries_query, 
    object_model=User, 
    stock_filters=[filters.beneficiary_filters], 
    caching_combinatory_strategy=metrics_cache.COUNT)

total_vendors_query = db.session.query(User)
total_vendors = metric.Metric(
    metric_name='total_vendors', 
    query=total_vendors_query, 
    object_model=User, 
    stock_filters=[filters.vendor_filters], 
    caching_combinatory_strategy=metrics_cache.COUNT)

has_transferred_count_query = db.session.query(func.count(func.distinct(CreditTransfer.sender_user_id)).label('count'))
has_transferred_count = metric.Metric(
    metric_name='has_transferred_count', 
    query=has_transferred_count_query, 
    object_model=CreditTransfer, 
    stock_filters=[filters.standard_payment_filters], 
    caching_combinatory_strategy=metrics_cache.FIRST_COUNT)
