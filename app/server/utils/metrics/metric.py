from server.utils.metrics import filters, metrics_cache
from server.utils.metrics.metrics_const import *

class Metric(object):
    metric_name = None
    filterable_by = []
    query = lambda: None
    stock_filters = []
    caching_combinatory_strategy = None
    object_model = None
    bypass_user_filters = False

    def execute_query(self, user_filters=[], date_filters=None, enable_caching=True):
        # Apply stock filters
        filtered_query = self.query
        for f in self.stock_filters:
            filtered_query = filtered_query.filter(*f)

        # Validate that the filters we're applying are in the metrics' filterable_by
        for f in user_filters or []:
            if f not in self.filterable_by:
                raise Exception(f'{self.metric_name} not filterable by {f}') 

        if DATE in self.filterable_by or []:
            filtered_query = filtered_query.filter(*date_filters)

        if not self.bypass_user_filters:
            filtered_query = filters.apply_filters(filtered_query, user_filters, self.object_model)

        return metrics_cache.execute_with_partial_history_cache(self.metric_name, filtered_query, self.object_model, self.caching_combinatory_strategy, enable_caching) 

    def __init__(self, metric_name, query=None, object_model=None, filterable_by=None, stock_filters=[], caching_combinatory_strategy=None, bypass_user_filters = False):
        self.metric_name = metric_name
        self.filterable_by = filterable_by
        self.query = query
        self.object_model = object_model
        self.stock_filters = stock_filters
        self.caching_combinatory_strategy = caching_combinatory_strategy
        self.bypass_user_filters = bypass_user_filters
