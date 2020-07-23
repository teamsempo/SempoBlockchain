# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

from server.utils.metrics import filters, metrics_cache, process_timeseries
from server.utils.metrics.metrics_const import *

class Metric(object):
    def execute_query(self, user_filters: dict = None, date_filters=None, enable_caching=True, population_query_result=False):
        user_filters = user_filters or {}
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
            
        result = metrics_cache.execute_with_partial_history_cache(self.metric_name, filtered_query, self.object_model, self.caching_combinatory_strategy, enable_caching) 
        if not self.timeseries_actions:
            return result

        return process_timeseries.process_timeseries(result, population_query_result, self.timeseries_actions)

        result = metrics_cache.execute_with_partial_history_cache(self.metric_name, filtered_query, self.object_model, self.caching_combinatory_strategy, enable_caching)
        if not self.timeseries_actions:
            return result

        return process_timeseries.process_timeseries(result, population_query_result, self.timeseries_actions)


    def __repr__(self):
        return f"<Metric {self.metric_name}>"

    def __init__(
            self,
            metric_name,
            query=None,
            object_model=None,
            filterable_by=None,
            stock_filters=None,
            caching_combinatory_strategy=None,
            bypass_user_filters=False,
            timeseries_actions=None,
    ):
        """
        :param metric_name: eg 'total_exchanged' or 'has_transferred_count'. Used for cache
        :param query: the based query that defines the aggregation process eg summing over transfers
        :param object_model: what the base object we're getting the metric for is (Transfers/Transfer Accounts/Users)
            used for applying filters with appropriate joins, and for cache
        :param filterable_by: used to validate whether the custom filters are valid for this case
        :param stock_filters: the base filters required to get this metric to return what we expect, regardless of what
        futher custom filtering we need to do
        :param caching_combinatory_strategy: how da cache gonna cache
        :param bypass_user_filters: ignore any user supplied filter
        """

        self.metric_name = metric_name
        self.filterable_by = filterable_by or []
        self.query = query or (lambda: None)
        self.object_model = object_model
        self.stock_filters = stock_filters or []
        self.caching_combinatory_strategy = caching_combinatory_strategy
        self.bypass_user_filters = bypass_user_filters
        self.timeseries_actions = timeseries_actions
