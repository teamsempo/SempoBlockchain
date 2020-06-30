from server.utils.metrics import filters, metrics_cache

class Metric(object):
    metric_name = None
    filterable_by = []
    query = lambda: None
    stock_filters = []
    caching_combinatory_strategy = None
    object_model = None

    def execute_query(self, user_filters=None, date_filters=None, enable_caching=True):
        # Handle stock filters
        filtered_query = self.query
        for f in self.stock_filters:
            filtered_query = filtered_query.filter(*f)

        filtered_query = filtered_query.filter(*date_filters)
        # Determine if caching is allowed
        return metrics_cache.execute_with_partial_history_cache(self.metric_name, filtered_query, self.object_model, self.caching_combinatory_strategy, enable_caching) 

    def __init__(self, metric_name, query = None, object_model = None, filterable_by = None, stock_filters = [], caching_combinatory_strategy = None):
        self.metric_name = metric_name
        self.filterable_by = filterable_by
        self.query = query
        self.object_model = object_model
        self.stock_filters = stock_filters
        self.caching_combinatory_strategy = caching_combinatory_strategy
