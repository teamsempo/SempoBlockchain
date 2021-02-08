from flask import Blueprint, request, g
from flask.views import MethodView
from server import db
from server.models.filter import Filter
from server.utils.auth import requires_auth
from server.schemas import new_filter_schema, new_filters_schema
from server.utils.transfer_filter import process_transfer_filters

new_filter_blueprint = Blueprint('filter', __name__)

class SavedFiltersAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def get(self):
        return {
            'message': 'success',
            'data': {'filters': new_filters_schema.dump(Filter.query.all()).data}
        }

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):
        post_data = request.get_json()

        filter_name = post_data.get('filter_name')
        filter = post_data.get('filter')

        if filter_name is None or filter is None or len(filter_name.strip()) == 0:
            return { 'message': 'Must provide a filter object and name' }, 400

        # Check that the filter is unique
        check_filter_name = Filter.query.filter_by(name=filter_name).all()
        if len(check_filter_name) != 0:
            return { 'message': 'Filter Name "{}" already used.'.format(filter_name) }, 400

        # Try to process the filter, just to validate that it works!
        try:
            process_transfer_filters(filter)
        except:
            return { 'message': f'Filter "{filter}" is invalid. Please provide a working filter!' }, 400

        created_filter = Filter(
            name=filter_name,
            filter=filter,
            organisation_id=g.active_organisation.id
        )

        db.session.add(created_filter)
        db.session.flush()

        response_object = {
            'message': 'success',
            'data': {'filter': new_filter_schema.dump(created_filter).data}
        }
        return response_object, 201

class SavedFilterAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def get(self, filter_id):
        f = Filter.query.filter(Filter.id == filter_id).first()
        if not f:
            return { 'message': f'Filter "{filter_id}" does not exist!' }, 404
        else:
            return {
                'message': 'success',
                'data': {'filter': new_filter_schema.dump(f).data}
            }
        
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def delete(self, filter_id):
        f = Filter.query.filter(Filter.id == filter_id).first()
        if not f:
            return { 'message': f'Filter "{filter_id}" does not exist!' }, 404
        else:
            db.session.delete(f)
            return {'message': 'success'}

new_filter_blueprint.add_url_rule(
    '/filter/',
    view_func=SavedFiltersAPI.as_view('filters_view'),
    methods=['GET', 'POST']
)

new_filter_blueprint.add_url_rule(
    '/filter/<int:filter_id>/',
    view_func=SavedFilterAPI.as_view('filter_view'),
    methods=['GET', 'DELETE']
)
