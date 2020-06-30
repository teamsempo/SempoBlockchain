from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccount
from sqlalchemy.sql import func
from server.utils.metrics import filters, metrics_cache, metric
from server import db, red, bt
from sqlalchemy.dialects.postgresql import JSONB

total_distributed_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
total_distributed = metric.Metric(
    metric_name='total_distributed', 
    query=total_distributed_query, 
    object_model=CreditTransfer, 
    stock_filters=[filters.disbursement_filters], 
    caching_combinatory_strategy=metrics_cache.SUM)

total_spent_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
total_spent = metric.Metric(
    metric_name='total_spent', 
    query=total_spent_query, 
    object_model=CreditTransfer, 
    stock_filters=[filters.standard_payment_filters], 
    caching_combinatory_strategy=metrics_cache.SUM)

total_exchanged_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('total'))
total_exchanged = metric.Metric(
    metric_name='total_exchanged', 
    query=total_exchanged_query, 
    object_model=CreditTransfer, 
    stock_filters=[filters.standard_payment_filters], 
    caching_combinatory_strategy=metrics_cache.SUM)

daily_transaction_volume_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('volume'),
        func.date_trunc('day', CreditTransfer.created).label('date')).group_by(func.date_trunc('day', CreditTransfer.created))
daily_transaction_volume = metric.Metric(
    metric_name='daily_transaction_volume', 
    query=daily_transaction_volume_query, 
    object_model=CreditTransfer, 
    stock_filters=[filters.standard_payment_filters], 
    caching_combinatory_strategy=metrics_cache.SUM_OBJECTS)

exhausted_balance_count_query = db.session.query(func.count(func.distinct(
    CreditTransfer.sender_transfer_account_id))
        .label('count')) \
        .join(CreditTransfer.sender_transfer_account)
exhausted_balance_count = metric.Metric(
    metric_name='exhausted_balance', 
    query=exhausted_balance_count_query, 
    object_model=CreditTransfer, 
    stock_filters=[filters.exhaused_balance_filters], 
    caching_combinatory_strategy=metrics_cache.FIRST_COUNT)

daily_disbursement_volume_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('volume'),
        func.date_trunc('day', CreditTransfer.created).label('date')).group_by(func.date_trunc('day', CreditTransfer.created))
daily_disbursement_volume = metric.Metric(
    metric_name='daily_disbursement_volume', 
    query=daily_disbursement_volume_query, 
    object_model=CreditTransfer, 
    stock_filters=[filters.disbursement_filters], 
    caching_combinatory_strategy=metrics_cache.SUM_OBJECTS)

transfer_use_breakdown_query = db.session.query(CreditTransfer.transfer_use.cast(JSONB),func.count(CreditTransfer.transfer_use)).group_by(CreditTransfer.transfer_use.cast(JSONB))
transfer_use_breakdown = metric.Metric(
    metric_name='transfer_use_breakdown', 
    query=transfer_use_breakdown_query, 
    object_model=CreditTransfer, 
    stock_filters=[filters.transfer_use_filters], 
    caching_combinatory_strategy=metrics_cache.QUERY_ALL)
