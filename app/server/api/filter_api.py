from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
from server import db
from server.models.saved_filter import SavedFilter
from server.utils.auth import requires_auth
from server.schemas import filters_schema, filter_schema

filter_blueprint = Blueprint('filters', __name__)


class SavedFiltersAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def get(self):

        filters = SavedFilter.query.all()

        if filters is None:
            response_object = {
                'message': 'No filters found'
            }

            return make_response(jsonify(response_object)), 400

        response_object = {
            'message': 'Successfully loaded saved filters',
            'data': {'filters': filters_schema.dump(filters).data}
        }

        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):
        post_data = request.get_json()

        filter_name = post_data.get('filter_name')
        filter_attributes = post_data.get('filter_attributes')

        if filter_name is None or filter_attributes is None or len(filter_name.strip()) == 0:
            response_object = {
                'message': 'Must provide a filter object and name'
            }
            return make_response(jsonify(response_object)), 400

        check_filter_name = SavedFilter.query.filter_by(name=filter_name).all()

        if len(check_filter_name) != 0:
            response_object = {
                'message': 'Filter Name "{}" already used.'.format(filter_name)
            }
            return make_response(jsonify(response_object)), 400

        create_filter = SavedFilter(
            name=filter_name,
            filter=filter_attributes,
            organisation_id=g.active_organisation.id
        )

        db.session.add(create_filter)
        db.session.flush()

        response_object = {
            'message': 'Filter {} created'.format(filter_name),
            'data': {'filter': filter_schema.dump(create_filter).data}
        }

        return make_response(jsonify(response_object)), 201


filter_blueprint.add_url_rule(
    '/filters/',
    view_func=SavedFiltersAPI.as_view('filters_view'),
    methods=['GET', 'POST']
)
