# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

from server.utils.metrics import filters, metrics_cache, postprocessing_actions, group
from server.utils.metrics.metrics_const import *

class Metric(object):
    def execute_query(self, user_filters: dict = None, date_filters_dict=None, enable_caching=True, population_query_result=False, dont_include_timeseries=False):
        """
        :param user_filters: dict of filters to apply to all metrics
        :param date_filters_dict: lookup table linking object models to their date filters (if applicable)  
        :param enable_caching: set to False if you don't want the query result to be cached
        :param population_query_result: This is a representation of the number of users over time, used in 
            post-processing of certian metrics. See postprocessing_actions.py for more details.
        :param dont_include_timeseries: if true, this skips calculating timeseries data and only fetches
             aggregated_query and total_query
        """
        actions = { 'query': self.query_actions, 'aggregated_query': self.aggregated_query_actions, 'total_query': self.total_query_actions }

        # Build the dict of queries to execute. Ungrouped metrics don't have aggregated queries,
        # and sometimes we only want aggregates and totals (based on dont_include_timeseries)
        if self.is_timeseries:
            if dont_include_timeseries:
                queries = { 'total_query': self.total_query }
            else:   
                queries = { 'query': self.query, 'total_query': self.total_query }
            if self.aggregated_query:
                queries['aggregated_query'] = self.aggregated_query
            if None in queries.values():
                raise Exception('Timeseries query requires a query, and a total_query')
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

            result = metrics_cache.execute_with_partial_history_cache(
                self.metric_name, 
                filtered_query, 
                self.object_model, 
                self.caching_combinatory_strategy, 
                enable_caching) 
            if not actions[query]:
                results[query] = result
            else:
                results[query] = postprocessing_actions.execute_postprocessing(result, population_query_result, actions[query])

        if self.is_timeseries:
            result = {}
            if not dont_include_timeseries:
                result['timeseries'] = results['query']
            if self.aggregated_query:
                result['aggregate'] = results['aggregated_query']
                result['aggregate']['total'] = results['total_query']
            else:
                result['aggregate'] = {'total': results['total_query']}
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
        :param is_timeseries: boolean indicating that the metric is a timeseries
        :param object_model: what the base object we're getting the metric for is (Transfers/Transfer Accounts/Users)
            used for applying filters with appropriate joins, and for cache
        :param filterable_by: used to validate whether the custom filters are valid for this case
        :param stock_filters: the base filters required to get this metric to return what we expect, regardless of what
        futher custom filtering we need to do
        :param caching_combinatory_strategy: how da cache gonna cache
        :param bypass_user_filters: ignore any user supplied filter
        :param query: the base query of the metric. This could be a timeseries query, or one which only returns a single number
        :param aggregated_query: used only with timeseries metrics, this is the query which defines an aggregated version 
            of the main query. For example, if the main query returns a timeseries representing number of transfer usages 
            over time, this query should get a non-timeseries of transfer usages spanning the entire time
        :param total_query: used only with timeseries metrics, this is a query which should return a single 
            value-- the total of the figure represenging the metric. For example, if the main query returns a timeseries of 
            transfer usages over time, this query should represent the summation of all transfer usages
        :param query_actions: Which post-processing actions are executed against the query after it runs. For more details, see
            postprocessing_actions.py
        :param aggregated_query_actions: query_actions for aggregated_query
        :param total_query_actions: query_actions for total_query
        :param groupable_attributes: list of attributes this metric is allowed to be grouped by
        """        
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
