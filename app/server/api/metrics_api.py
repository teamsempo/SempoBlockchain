from flask import Blueprint, request, make_response, jsonify, g
import json

from server.utils.metrics.metrics import calculate_transfer_stats
from server.utils.metrics import metrics_const
from flask.views import MethodView
from server.utils.transfer_filter import ALL_FILTERS, TRANSFER_FILTERS, USER_FILTERS, process_transfer_filters
from server.utils.auth import requires_auth

metrics_blueprint = Blueprint('metrics', __name__)

class CreditTransferStatsApi(MethodView):
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
            - metric_type: (Default: ALL) Allows the user to swtich between `transfer`, `participant`, and `all`
        """

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        encoded_filters = request.args.get('params')
        disable_cache = request.args.get('disable_cache', 'False').lower() in ['true', '1']  # Defaults to bool false
        metric_type = request.args.get('metric_type', metrics_const.ALL)

        if metric_type not in metrics_const.METRIC_TYPES:
            raise Exception(f'{metric_type} not a valid type. Please choose one of the following: {", ".join(metrics_const.METRIC_TYPES)}')

        filters = process_transfer_filters(encoded_filters)
        transfer_stats = calculate_transfer_stats(
            start_date=start_date,
            end_date=end_date,
            user_filter=filters,
            metric_type=metric_type,
            disable_cache=disable_cache
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
        METRIC_TYPES_FILTERS = {
            metrics_const.ALL: ALL_FILTERS,
            metrics_const.USER: USER_FILTERS,
            metrics_const.TRANSFER: TRANSFER_FILTERS,
        }

        response_object = {
            'status' : 'success',
            'message': 'Successfully Loaded.',
            'data': {
                'filters': json.dumps(METRIC_TYPES_FILTERS[metric_type])
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
