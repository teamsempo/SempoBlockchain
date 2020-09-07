from flask import Blueprint, g, make_response, jsonify, request
from flask.views import MethodView

from server import db
from server.models.attribute_map import AttributeMap
from server.schemas import attribute_maps_schema, attribute_map_schema
from server.utils.auth import requires_auth

attribute_map_blueprint = Blueprint('attribute_map', __name__)


class AttributeMapAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def get(self, attribute_map_id):

        if attribute_map_id:
            attribute_map = AttributeMap.query.get(attribute_map_id)

            if not attribute_map:
                response_object = {
                    'message': 'Attribute map not found'
                }
                return make_response(jsonify(response_object)), 404

            response_object = {
                'data': attribute_map_schema.dump(attribute_map).data
            }
            return make_response(jsonify(response_object)), 200

        attribute_maps = AttributeMap.query.filter_by(organisation=g.active_organisation).all()

        response_object = {
            'data': {'attribute_maps': attribute_maps_schema.dump(attribute_maps).data}
        }
        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def post(self, attribute_map_id):
        data = request.get_json()

        input_name = data.get('input_name', '')
        output_name = data.get('output_name', '')

        if input_name == '' or output_name == '':
            response_object = {
                'message': 'Attribute names must be defined'
            }
            return make_response(jsonify(response_object)), 400

        existing_map = AttributeMap.query.filter_by(input_name=input_name).first()

        if existing_map:
            existing_map.output_name = output_name
        else:
            am = AttributeMap(input_name, output_name, g.active_organisation)
            db.session.add(am)

        db.session.commit()

        response_object = {
            'message': 'Attributed Added'
        }
        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def delete(self, attribute_map_id):

        existing_map = AttributeMap.query.get(attribute_map_id)

        if not existing_map:
            response_object = {
                'message': f'Attribute map not found for id: {attribute_map_id}'
            }
            return make_response(jsonify(response_object)), 404

        db.session.delete(existing_map)

        db.session.commit()

        response_object = {
            'message': 'Attributed Deleted'
        }
        return make_response(jsonify(response_object)), 200


attribute_map_blueprint.add_url_rule(
    '/attribute_map/<int:attribute_map_id>/',
    view_func=AttributeMapAPI.as_view('single_attribute_map_view'),
    methods=['GET', 'DELETE']
)

attribute_map_blueprint.add_url_rule(
    '/attribute_map/',
    view_func=AttributeMapAPI.as_view('attribute_map_view'),
    methods=['GET', 'POST'],
    defaults={'attribute_map_id': None}
)