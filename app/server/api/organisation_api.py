from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db
from server.models.organisation import Organisation
from server.models.models import Token
from server.models.utils import paginate_query
from server.models.user import User
from server.models.transfer_account import TransferAccount
from server.schemas import organisation_schema, organisations_schema
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

                return make_response(jsonify(response_object)), 400

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

        name = post_data.get('name')
        token_id = post_data.get('token_id')

        if name is None:
            return make_response(jsonify({'message': 'Must provide name to create organisation.'})), 401

        existing_organisation = Organisation.query.filter_by(name=name).execution_options(show_all=True).first()
        if existing_organisation is not None:
            return make_response(
                jsonify({
                    'message': 'Must be unique name. Organisation already exists for name: {}'.format(name),
                    'data': {'organisation': organisation_schema.dump(existing_organisation).data}
                })), 400

        token = Token.query.get(token_id)
        if token is None:
            return make_response(jsonify({'message': 'Token not found'})), 404

        new_organisation = Organisation(name=name, token=token)

        transfer_account = TransferAccount(organisation=new_organisation)

        db.session.add_all([new_organisation, transfer_account])
        db.session.commit()

        new_organisation.org_level_transfer_account_id = transfer_account.id

        db.session.commit()

        response_object = {
            'message': 'Created Organisation',
            'data': {'organisation': organisation_schema.dump(new_organisation).data},
        }

        return make_response(jsonify(response_object)), 201


class OrganisationUserAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def put(self, organisation_id):
        put_data = request.get_json()

        user_ids = put_data.get('user_ids')

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
                user.organisations.append(organisation)
                user.default_organisation = organisation
                db.session.commit()

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
    '/organisation/<int:organisation_id>/',
    view_func=OrganisationAPI.as_view('single_organisation_view'),
    methods=['GET', 'PUT']
)

organisation_blueprint.add_url_rule(
    '/organisation/<int:organisation_id>/users',
    view_func=OrganisationUserAPI.as_view('organisation_user_view'),
    methods=['PUT'],
)
