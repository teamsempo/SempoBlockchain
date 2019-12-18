from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db
from server.models.organisation import Organisation
from server.models.token import Token
from server.models.utils import paginate_query
from server.models.user import User
from server.schemas import organisation_schema, organisations_schema
from server.utils.contract import deploy_cic_token
from server.utils.auth import requires_auth, show_all

organisation_blueprint = Blueprint('organisation', __name__)


# only allow Sempo Admins to interact with Organisation API
class OrganisationAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def get(self, organisation_id):

        if organisation_id:
            organisation = Organisation.query.execution_options(show_all=True).get(organisation_id)

            if organisation is None:
                response_object = {
                    'message': 'No such organisation: {}'.format(organisation_id),
                }

                return make_response(jsonify(response_object)), 404

            response_object = {
                'message': 'Successfully Loaded Organisation',
                'data': {'organisation': organisation_schema.dump(organisation).data, }
            }
            return make_response(jsonify(response_object)), 200

        else:
            organisations_query = Organisation.query.execution_options(show_all=True)

            organisations, total_items, total_pages = paginate_query(organisations_query, Organisation)

            if organisations is None:
                return make_response(jsonify({'message': 'No organisations found'})), 400

            response_object = {
                'message': 'Successfully Loaded All Organisations',
                'items': total_items,
                'pages': total_pages,
                'data': {'organisations': organisations_schema.dump(organisations).data}
            }
            return make_response(jsonify(response_object)), 200

    @show_all
    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self, organisation_id):
        post_data = request.get_json()

        organisation_name = post_data.get('organisation_name')
        token_id = post_data.get('token_id')

        deploy_cic = post_data.get('deploy_cic', False)

        if organisation_name is None:
            return make_response(jsonify({'message': 'Must provide name to create organisation.'})), 400

        existing_organisation = Organisation.query.filter_by(name=organisation_name).execution_options(show_all=True).first()
        if existing_organisation is not None:
            return make_response(
                jsonify({
                    'message': 'Must be unique name. Organisation already exists for name: {}'.format(organisation_name),
                    'data': {'organisation': organisation_schema.dump(existing_organisation).data}
                })), 400

        new_organisation = Organisation(name=organisation_name)
        db.session.add(new_organisation)
        db.session.flush()

        response_object = {
            'message': 'Created Organisation',
            'data': {'organisation': organisation_schema.dump(new_organisation).data},
        }

        if token_id:
            token = Token.query.get(token_id)
            if token is None:
                return make_response(jsonify({'message': 'Token not found'})), 404
            new_organisation.bind_token(token)

        elif deploy_cic:

            cic_response_object, cic_response_code = deploy_cic_token(post_data, new_organisation)
            if cic_response_code == 201:
                response_object['data']['token_id'] = cic_response_object['data']['token_id']
            else:
                return make_response(jsonify(cic_response_object)), cic_response_code

        return make_response(jsonify(response_object)), 201


class OrganisationUserAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def put(self, organisation_id):
        put_data = request.get_json()

        user_ids = put_data.get('user_ids')
        is_admin = put_data.get('is_admin', False)

        if len(user_ids) == 0:
            return make_response(jsonify({'message': 'Must provide a list of user ids'})), 400

        if organisation_id is None:
            return make_response(jsonify({'message': 'Must provide organisation ID'})), 400

        organisation = Organisation.query.execution_options(show_all=True).get(organisation_id)

        if organisation is None:
            return make_response(jsonify({'message': 'No organisation found for ID: {}'.format(organisation_id)}))

        diagnostics = []
        for user_id in user_ids:
            user = User.query.execution_options(show_all=True).get(user_id)

            if user is None:
                diagnostics.append({'user': user_id, 'message': 'No user exists'})

            else:
                user.add_user_to_organisation(organisation, is_admin)

        response_object = {
            'message': 'Tied users to organisation {}'.format(organisation_id),
            'diagnostics': diagnostics,
            'data': {'organisation': organisation_schema.dump(organisation).data}
        }

        return make_response(jsonify(response_object)), 200


# add Rules for API Endpoints
organisation_blueprint.add_url_rule(
    '/organisation/',
    view_func=OrganisationAPI.as_view('organisation_view'),
    methods=['GET', 'PUT', 'POST'],
    defaults={'organisation_id': None}
)

organisation_blueprint.add_url_rule(
    '/organisation/<int:organisation_id>',
    view_func=OrganisationAPI.as_view('single_organisation_view'),
    methods=['GET', 'PUT']
)

organisation_blueprint.add_url_rule(
    '/organisation/<int:organisation_id>/users',
    view_func=OrganisationUserAPI.as_view('organisation_user_view'),
    methods=['PUT'],
)
