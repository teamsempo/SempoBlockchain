# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

from server.utils.metrics import filters, metrics_cache, process_timeseries, group
from server.utils.metrics.metrics_const import *

class Metric(object):
    # TODO: Docs here
    def execute_query(self, user_filters: dict = None, date_filters_dict=None, enable_caching=True, population_query_result=False):
        actions = { 'query': self.query_actions, 'aggregated_query': self.aggregated_query_actions, 'total_query': self.total_query_actions }
        if self.is_timeseries:
            queries = { 'query': self.query, 'aggregated_query': self.aggregated_query, 'total_query': self.total_query }
            if None in queries.values():
                raise Exception('Timeseries query requires a query, aggregated_query, and a total_query')
        else:
            queries = { 'query': self.query }

        results = {}
        for query in queries:
            user_filters = user_filters or {}
            # Apply stock filters
            filtered_query = queries[query]
            for f in self.stock_filters:
                filtered_query = filtered_query.filter(*f)

            # Validate that the filters we're applying are in the metrics' filterable_by
            for f in user_filters or []:
                if f not in self.filterable_by:
                    raise Exception(f'{self.metric_name} not filterable by {f}')
            # Apply the applicable date filters
            if DATE in self.filterable_by or []:
                if date_filters_dict:
                    date_filters = date_filters_dict[self.object_model]
                    filtered_query = filtered_query.filter(*date_filters)

            if not self.bypass_user_filters:
                filtered_query = filters.apply_filters(filtered_query, user_filters, self.object_model)

            result = metrics_cache.execute_with_partial_history_cache(self.metric_name, filtered_query, self.object_model, self.caching_combinatory_strategy, enable_caching) 
            if not actions[query]:
                results[query] = result
            else:
                results[query] = process_timeseries.process_timeseries(result, population_query_result, actions[query])
        
        if self.is_timeseries:
            result = {}
            result['timeseries'] = results['query']
            result['aggregate'] = results['aggregated_query']
            result['aggregate']['total'] = results['total_query']
            return result
        else:
            return results['query']

    def __repr__(self):
        return f"<Metric {self.metric_name}>"

    def __init__(
            self,
            metric_name,
            is_timeseries = False,
            object_model=None,
            filterable_by=None,
            stock_filters=None,
            caching_combinatory_strategy=None,
            bypass_user_filters=False,
            query=None,
            aggregated_query=None,
            total_query=None,
            query_actions=None,
            aggregated_query_actions=None,
            total_query_actions=None,
            groupable_attributes=[]
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
        # TODO: Update the docs here^ 

        
        self.metric_name = metric_name
        self.is_timeseries = is_timeseries
        self.filterable_by = filterable_by or []
        self.object_model = object_model
        self.stock_filters = stock_filters or []
        self.caching_combinatory_strategy = caching_combinatory_strategy
        self.bypass_user_filters = bypass_user_filters
        # Queries
        self.query = query # Base Query (Everything has one of these)
        self.aggregated_query = aggregated_query # Aggregated Query (All/Only Timeseries Queries have this)
        self.total_query = total_query # Total Query (All/Only Timeseries Queries have this)
        # Query Actions
        self.query_actions = query_actions
        self.aggregated_query_actions = aggregated_query_actions
        self.total_query_actions = total_query_actions

        self.groupable_attributes = groupable_attributes
