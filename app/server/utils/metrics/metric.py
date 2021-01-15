# Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
# The code in this file is not included in the GPL license applied to this repository
# Unauthorized copying of this file, via any medium is strictly prohibited

from server.utils.metrics import filters, metrics_cache, postprocessing_actions, group
from server.utils.metrics.metrics_const import *
import datetime
from server import db

class Metric(object):
    def execute_query(self, user_filters: dict = None, date_filter_attributes=None, enable_caching=True, population_query_result=False, dont_include_timeseries=False, start_date=None, end_date=None, group_by=None):
        """
        :param user_filters: dict of filters to apply to all metrics
        :param date_filter_attributes: lookup table indicating which row to use when filtering by date  
        :param enable_caching: set to False if you don't want the query result to be cached
        :param population_query_result: This is a representation of the number of users over time, used in 
            post-processing of certian metrics. See postprocessing_actions.py for more details.
        :param dont_include_timeseries: if true, this skips calculating timeseries data and only fetches
             aggregated_query and total_query
        :param start_date: Start date for metrics queries (for calculating percent change within date range)
        :param End_date: End date for metrics queries (for calculating percent change within date range)
        :param group_by: Name of the group-by used, used for metrics cache key names
        """
        actions = {
                    'primary': self.query_actions, 
                    'aggregated_query': self.aggregated_query_actions, 
                    'total_query': self.total_query_actions,
                    'start_day_query': self.total_query_actions,
                    'end_day_query': self.total_query_actions
                }

        # Build the dict of queries to execute. Ungrouped metrics don't have aggregated queries,
        # and sometimes we only want aggregates and totals (based on dont_include_timeseries)
        if self.is_timeseries:
            if dont_include_timeseries:
                queries = { 'total_query': self.total_query, 'start_day_query': self.total_query, 'end_day_query': self.total_query }
            else:   
                queries = { 'primary': self.query, 'total_query': self.total_query, 'start_day_query': self.total_query, 'end_day_query': self.total_query }
            if self.aggregated_query:
                queries['aggregated_query'] = self.aggregated_query
            if None in queries.values():
                raise Exception('Timeseries query requires a query, and a total_query')
        else:
            queries = { 'primary': self.query }

        results = {}
        for query in queries:
            user_filters = user_filters or {}
            # Apply stock filters
            filtered_query = queries[query]
            for f in self.stock_filters:
                filtered_query = filtered_query.filter(*f)

            # Validate that the filters we're applying are in the metrics' filterable_by
            for f, _ in user_filters or []:
                if f not in self.filterable_by:
                    raise Exception(f'{self.metric_name} not filterable by {f}')

            # Apply the applicable date filters
            if DATE in self.filterable_by or []:
                if start_date or end_date:
                    date_filter_attribute = date_filter_attributes[self.object_model]
                    date_filters = []
                    if start_date:
                        date_filters.append(date_filter_attribute >= start_date)
                    if end_date:
                        date_filters.append(date_filter_attribute <=  datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)  )
                    filtered_query = filtered_query.filter(*date_filters)

            # Handle start_day and end_day queries so we can have a percentage change for the whole day range
            if query in ['start_day_query', 'end_day_query']:
                date_filter_attribute = date_filter_attributes[self.object_model]
                # If a user provided end-date goes past today, just use today. Also if the user doesn't provide a day
                # also use today
                today = datetime.datetime.now().replace(minute=0, hour=0, second=0, microsecond=0)
                if not end_date or datetime.datetime.strptime(end_date, "%Y-%m-%d") > today:
                    last_day = today
                else:
                    last_day = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                if not start_date:
                    # Get first date where data is present if no other date is given
                    first_day = db.session.query(db.func.min(date_filter_attribute)).scalar() or today
                else:
                    first_day = datetime.datetime.strptime(start_date, "%Y-%m-%d")

                day = first_day if query == 'start_day_query' else last_day

                date_filters = []
                # To filter for items on day n, we have to filter between day n and day n+1
                date_filters.append(date_filter_attribute >= day)
                date_filters.append(date_filter_attribute <=  day + datetime.timedelta(days=1)  )
                filtered_query = filtered_query.filter(*date_filters)

            if not self.bypass_user_filters:
                filtered_query = filters.apply_filters(filtered_query, user_filters, self.object_model)

            strategy = self.caching_combinatory_strategy
            if self.is_timeseries and query=='primary':
                strategy = self.timeseries_caching_combinatory_strategy

            result = metrics_cache.execute_with_partial_history_cache(
                self.metric_name, 
                filtered_query, 
                self.object_model, 
                strategy, 
                enable_caching,
                group_by=group_by)

            if not actions[query]:
                results[query] = result
            else:
                results[query] = postprocessing_actions.execute_postprocessing(result, population_query_result, actions[query])
        if self.is_timeseries:
            result = {}
            # Get percentage change between first and last date
            start_value = results['start_day_query'] if 'start_day_query' in results else 0
            end_value = results['end_day_query'] if 'end_day_query' in results else 0
            try:
                increase = float(end_value) - float(start_value)
                percent_change = (increase / float(start_value)) * 100
            except ZeroDivisionError:
                percent_change = None 

            if self.value_type not in VALUE_TYPES:
                raise Exception(f'{self.value_type} not a valid metric type!')
            result['type'] = {
                'value_type': self.value_type,
                'display_decimals': 2 if self.value_type == COUNT_AVERAGE else 0
            }
            if self.token:
                result['type']['currency_name'] = self.token.name
                result['type']['currency_symbol'] = self.token.symbol
                result['type']['display_decimals'] = self.token.display_decimals if self.token.display_decimals else 0
            if not dont_include_timeseries:
                result['timeseries'] = results['primary']
            if self.aggregated_query:
                result['aggregate'] = results['aggregated_query']
                result['aggregate']['total'] = results['total_query']
                result['aggregate']['percent_change'] = percent_change
            else:
                result['aggregate'] = {'total': results['total_query'], 'percent_change': percent_change}
            return result
        else:
            return results['primary']

    def __repr__(self):
        return f"<Metric {self.metric_name}>"

    def __init__(
            self,
            metric_name,
            is_timeseries = False,
            object_model=None,
            filterable_by=None,
            stock_filters=None,
            timeseries_caching_combinatory_strategy=None,
            caching_combinatory_strategy=None,
            bypass_user_filters=False,
            query=None,
            aggregated_query=None,
            total_query=None,
            query_actions=None,
            aggregated_query_actions=None,
            total_query_actions=None,
            groupable_attributes=[],
            value_type=COUNT,
            token=None
        ):
        """
        :param metric_name: eg 'total_exchanged' or 'has_transferred_count'. Used for cache
        :param is_timeseries: boolean indicating that the metric is a timeseries
        :param object_model: what the base object we're getting the metric for is (Transfers/Transfer Accounts/Users)
            used for applying filters with appropriate joins, and for cache
        :param filterable_by: used to validate whether the custom filters are valid for this case
        :param stock_filters: the base filters required to get this metric to return what we expect, regardless of what
        futher custom filtering we need to do
        :param timeseries_caching_combinatory_strategy: how new and old timeseries results will be combined
        :param caching_combinatory_strategy: how new and old non-timeseries results will be combined
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
        :param value_type: type of metric (count, currency)
        :param token: Token obj to determine label attributable to the metric (Dollars, Euro, etc...)
        """        
        self.metric_name = metric_name
        self.is_timeseries = is_timeseries
        self.filterable_by = filterable_by or []
        self.object_model = object_model
        self.stock_filters = stock_filters or []
        self.timeseries_caching_combinatory_strategy = timeseries_caching_combinatory_strategy
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
        self.value_type = value_type
        self.token = token
