from flask import Blueprint, request, make_response, jsonify, g
import json

from server.utils.metrics.metrics import calculate_transfer_stats
from server.utils.metrics import metrics_const, metrics_cache
from server.utils.metrics.group import Groups
from flask.views import MethodView
from server.utils.transfer_filter import Filters, process_transfer_filters
from server.utils.auth import requires_auth, multi_org

metrics_blueprint = Blueprint('metrics', __name__)

class CreditTransferStatsApi(MethodView):
    @multi_org
    @requires_auth(allowed_roles={'ADMIN': 'any'})
    def get(self):
        """
        This endpoint generates metrics for both transfers and participants.
        By default, it returns all metric types, but can provide a certian type of metric with the metric_type 
        parameter. When requesting `transfer` metric types, all `encoded_filters` are applicable, but only
        a subset are applicable to `participant` metrics. To see which metrics are applicable to which metric type,
        see documentation for the `/metrics/filters/` endpoint.
        Parameters:
            - start_date: (Default: None) Start date string of range to query. Format: "2020-01-01T15:00:00.000Z"
            - end_date: (Default: None) End date string of range to query. Format: "2020-01-01T15:00:00.000Z"
            - encoded_filters: (Default: None) Set of filters to apply to the metrics query. 
                Additional documentation for filters can be found in /utils/transfer_filter.py
            - disable_cache: (Default: False) Force-disables cache
            - metric_type: (Default: 'all') Allows the user to swtich between `transfer`, `participant`, and `all`
            - timeseries_unit: (Default: 'day') Allows the user to swtich between `day`, `week`, `month` and `year`
            - group_by: (Default: 'ungrouped') Allows the user to swtich choose group_by category. See /metrics/filters for all options
            - token_id: (Default: None) If multi-org is being used, and the orgs have different tokens, this lets the user choose
                which token's stats to present
        """
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        encoded_filters = request.args.get('params')

        disable_cache = request.args.get('disable_cache', 'False').lower() in ['true', '1']  # Defaults to bool false
        metric_type = request.args.get('metric_type', metrics_const.ALL)
        requested_metric = request.args.get('requested_metric', metrics_const.ALL)
        timeseries_unit = request.args.get('timeseries_unit', metrics_const.DAY)
        group_by = request.args.get('group_by', metrics_const.UNGROUPED)
        token_id = request.args.get('token_id', None)

        if timeseries_unit not in metrics_const.TIMESERIES_UNITS:
            raise Exception(f'{timeseries_unit} not a valid timeseries unit. Please choose one of the following: {", ".join(metrics_const.TIMESERIES_UNITS)}')

        if metric_type not in metrics_const.METRIC_TYPES:
            raise Exception(f'{metric_type} not a valid metric type. Please choose one of the following: {", ".join(metrics_const.METRIC_TYPES)}')

        groups = Groups()
        if group_by not in groups.GROUP_TYPES.keys():
            raise Exception(f'{group_by} not a valid grouping type. Please choose one of the following: {", ".join(groups.GROUP_TYPES.keys())}')


        filters = process_transfer_filters(encoded_filters)

        transfer_stats = calculate_transfer_stats(
            start_date=start_date,
            end_date=end_date,
            user_filter=filters,
            metric_type=metric_type,
            requested_metric=requested_metric,
            disable_cache=disable_cache,
            timeseries_unit = timeseries_unit,
            group_by = group_by,
            token_id = token_id
        )

        response_object = {
            'status': 'success',
            'message': 'Successfully Loaded.',
            'data': {
                'transfer_stats': transfer_stats
            }
        }

        return make_response(jsonify(response_object)), 200

class FiltersApi(MethodView):
    @multi_org
    @requires_auth(allowed_roles={'ADMIN': 'any'})
    def get(self):
        """
        This endpoint provides JSON documentation as to which filters are applicable to which metric types
        Parameters:
            - metric_type: (Default: ALL) Allows the user to request filters for `transfer`, `participant`, and `all`
        """

        metric_type = request.args.get('metric_type', metrics_const.ALL)
        if metric_type not in metrics_const.METRIC_TYPES:
            raise Exception(f'{metric_type} not a valid type. Please choose one of the following: {", ".join(metrics_const.METRIC_TYPES)}')
        filters = Filters()
        METRIC_TYPES_FILTERS = {
            metrics_const.ALL: filters.ALL_FILTERS,
            metrics_const.USER: filters.USER_FILTERS,
            metrics_const.TRANSFER: filters.TRANSFER_FILTERS,
        }

        group_objects = Groups()
        GROUP_TYPES_FILTERS = {
            metrics_const.ALL: group_objects.GROUP_TYPES,
            metrics_const.USER: group_objects.USER_GROUPS,
            metrics_const.TRANSFER: group_objects.TRANSFER_GROUPS,
        }
        groups = {}
        group_filters = GROUP_TYPES_FILTERS[metric_type]
        for f in group_filters:
            # Filter out coordinates at the API level, since we don't want to show them as groupable options
            # But we do require them to be groupable in practice for the map page
            if f in ['sender,coordinates', 'recipient,coordinates']:
                continue
            if group_filters[f]:
                groups[f] = group_filters[f].get_api_representation()
            else:
                groups[f] = {'name': 'Ungrouped'}
        response_object = {
            'status' : 'success',
            'message': 'Successfully Loaded.',
            'data': {
                'filters': METRIC_TYPES_FILTERS[metric_type],
                'groups': groups
            }
        }

        return make_response(jsonify(response_object)), 200

class CacheApi(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self):
        """
        This endpoint erases the cache for the current org. 
        Use this after you alter the past so the cache can rebuild itself 
        """
        count = metrics_cache.clear_metrics_cache()

        response_object = {
            'status' : 'success',
            'message': 'Cache erased',
            'data': {
                'removed_entries': count,
            }
        }
        return make_response(jsonify(response_object)), 200

metrics_blueprint.add_url_rule(
    '/metrics/',
    view_func=CreditTransferStatsApi.as_view('metrics_view'),
    methods=['GET']
)

metrics_blueprint.add_url_rule(
    '/metrics/filters/',
    view_func=FiltersApi.as_view('metrics_filters_view'),
    methods=['GET']
)

metrics_blueprint.add_url_rule(
    '/metrics/clear_cache/',
    view_func=CacheApi.as_view('metrics_cache_view'),
    methods=['POST']
)
