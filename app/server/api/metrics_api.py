from flask import Blueprint, request, make_response, jsonify
import json

from server.utils.metrics.metrics import calculate_transfer_stats
from server.utils.metrics import metrics_const
from flask.views import MethodView
from server.utils.transfer_filter import TRANSFER_FILTERS, process_transfer_filters
from server.utils.auth import requires_auth

metrics_blueprint = Blueprint('metrics', __name__)

class CreditTransferStatsApi(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'any'})
    def get(self):

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        encoded_filters = request.args.get('params')
        metric_type = request.args.get('metric_type', metrics_const.ALL)
        if metric_type not in metrics_const.METRIC_TYPES:
            raise Exception(f'{metric_type} not a valid type. Please choose one of the following: {", ".join(metrics_const.METRIC_TYPES)}')

        filters = process_transfer_filters(encoded_filters)
        transfer_stats = calculate_transfer_stats(start_date=start_date, end_date=end_date, user_filter=filters, metric_type=metric_type)

        response_object = {
            'status': 'success',
            'message': 'Successfully Loaded.',
            'data': {
                'transfer_stats': transfer_stats
            }
        }

        return make_response(jsonify(response_object)), 200

class CreditTransferFiltersApi(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'any'})
    def get(self):
        response_object = {
            'status' : 'success',
            'message': 'Successfully Loaded.',
            'data': {
                'filters': json.dumps(TRANSFER_FILTERS)
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
    view_func=CreditTransferFiltersApi.as_view('metrics_filters_view'),
    methods=['GET']
)