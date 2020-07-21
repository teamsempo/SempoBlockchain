from sqlalchemy.sql import func, distinct

from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccount

from server.models.user import User
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage

from server.utils.metrics import filters, metrics_cache, metric, process_timeseries, metric_group
from server.utils.metrics.metrics_const import *

from server import db, red, bt
from sqlalchemy.dialects.postgresql import JSONB

class TransferStats(metric_group.MetricGroup):
    def __init__(self, timeseries_unit = 'day'):
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
            filterable_by=self.filterable_attributes))

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

        transfer_use_breakdown_query = db.session.query(CreditTransfer.transfer_use.cast(JSONB),func.count(CreditTransfer.transfer_use)).group_by(CreditTransfer.transfer_use.cast(JSONB))
        self.metrics.append(metric.Metric(
            metric_name='transfer_use_breakdown', 
            query=transfer_use_breakdown_query, 
            object_model=CreditTransfer, 
            stock_filters=[filters.transfer_use_filters], 
            caching_combinatory_strategy=metrics_cache.QUERY_ALL,
            filterable_by=self.filterable_attributes))

        # Timeseries Metrics
        disbursement_volume_timeseries_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('volume'),
                func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date')).group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created))
        self.metrics.append(metric.Metric(
            metric_name='daily_disbursement_volume', # Will rename when API breaking changes come in
            query=disbursement_volume_timeseries_query, 
            object_model=CreditTransfer, 
            stock_filters=[filters.disbursement_filters], 
            caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
            filterable_by=self.filterable_attributes,
            # Will add AGGREGATE_FORMATTED_TIMESERIES when FE is ready for it,
            # or metrics PR
            timeseries_actions=[FORMAT_TIMESERIES]))

        transaction_volume_timeseries_query = db.session.query(func.sum(CreditTransfer.transfer_amount).label('volume'),
                func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date')).group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created))
        self.metrics.append(metric.Metric(
            metric_name='daily_transaction_volume', # Will rename when API breaking changes come in
            query=transaction_volume_timeseries_query, 
            object_model=CreditTransfer, 
            stock_filters=[filters.standard_payment_filters], 
            caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
            filterable_by=self.filterable_attributes,
            # Will add AGGREGATE_FORMATTED_TIMESERIES when FE is ready for it,
            # or metrics PR
            timeseries_actions=[FORMAT_TIMESERIES]))

        transaction_count_query = db.session.query(func.count(CreditTransfer.id).label('volume'),
                func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date')).group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created))
        self.metrics.append(metric.Metric(
            metric_name='daily_transaction_count',
            query=transaction_count_query, 
            object_model=CreditTransfer, 
            stock_filters=[filters.standard_payment_filters], 
            caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
            filterable_by=self.filterable_attributes,
            timeseries_actions=[FORMAT_TIMESERIES, AGGREGATE_FORMATTED_TIMESERIES]))

        self.metrics.append(metric.Metric(
            metric_name='transfer_amount_per_user',
            query=transaction_volume_timeseries_query, 
            object_model=CreditTransfer, 
            stock_filters=[filters.standard_payment_filters], 
            caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
            filterable_by=self.filterable_attributes,
            timeseries_actions=[CALCULATE_PER_USER, FORMAT_TIMESERIES, AGGREGATE_FORMATTED_TIMESERIES]))

        self.metrics.append(metric.Metric(
            metric_name='trades_per_user',
            query=transaction_count_query, 
            object_model=CreditTransfer, 
            stock_filters=[filters.standard_payment_filters], 
            caching_combinatory_strategy=metrics_cache.SUM_OBJECTS,
            filterable_by=self.filterable_attributes,
            timeseries_actions=[CALCULATE_PER_USER, FORMAT_TIMESERIES, AGGREGATE_FORMATTED_TIMESERIES]))

        #transaction_count_query = db.session.query(func.count(CreditTransfer.id).label('volume'),
        #        func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date'), User.id).group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created)).group_by(User.id)
        #transaction_count_query.join(CreditTransfer, User.id == CreditTransfer.sender_user_id)
        

        
        # transfer_mode
        subquery = db.session.query(User.id).join(CustomAttributeUserStorage, CustomAttributeUserStorage.user_id == User.id)\
            .filter(CustomAttributeUserStorage.name == 'gender')

        transaction_count_query = db.session.query(func.count(CreditTransfer.id).label('volume'),
                func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date'))\
                .group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created))\
            .filter(User.id.notin_(subquery))
            #.join(CustomAttributeUserStorage, User.id == CustomAttributeUserStorage.user_id)
        print('zzz')
        print(transaction_count_query.all())
        #for a in transaction_count_query.all():
        #    print(a)
        #print('zzz')

        
        transaction_count_query = db.session.query(func.count(CreditTransfer.id).label('volume'),
                func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date'), CustomAttributeUserStorage.value)\
                    .group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created))\
                    .group_by(CustomAttributeUserStorage.value)\
            .join(User, CreditTransfer.recipient_user_id == User.id)\
            .join(CustomAttributeUserStorage, User.id == CustomAttributeUserStorage.user_id)\
            .filter(CustomAttributeUserStorage.name == 'gender')
        print(transaction_count_query.all())

        #for a in transaction_count_query.all():
        #    print(a)
        #print('zzz')
        
        #transaction_count_query = db.session.query(func.count(CreditTransfer.id).label('volume'),
        #        func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date'), 
        #        CreditTransfer.transfer_mode)\
        #        .group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created))\
        #        .group_by(CreditTransfer.transfer_mode)
        #transaction_count_query.join(CreditTransfer, User.id == CreditTransfer.sender_user_id)

        #transaction_count_query = db.session.query(func.count(CreditTransfer.id).label('volume'),
        #        func.date_trunc(self.timeseries_unit, CreditTransfer.created).label('date'), 
        #        User.id)\
        #        .group_by(func.date_trunc(self.timeseries_unit, CreditTransfer.created))\
        #        .group_by(User.id)
        #transaction_count_query.join(CreditTransfer, User.id == CreditTransfer.sender_user_id)
