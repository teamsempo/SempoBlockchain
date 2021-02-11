from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.models.organisation import Organisation
from server.models.token import Token
from server.models.utils import paginate_query
from server.models.user import User
from server.schemas import organisation_schema, organisations_schema
from server.utils.contract import deploy_cic_token
from server.utils.auth import requires_auth, show_all
from server.constants import ISO_COUNTRIES, ASSIGNABLE_TIERS
import pendulum
from server.utils.access_control import AccessControl

organisation_blueprint = Blueprint('organisation', __name__)

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

            organisations, total_items, total_pages, new_last_fetched = paginate_query(organisations_query)

            if organisations is None:
                return make_response(jsonify({'message': 'No organisations found'})), 400

            response_object = {
                'message': 'Successfully Loaded All Organisations',
                'items': total_items,
                'pages': total_pages,
                'last_fetched': new_last_fetched,
                'data': {'organisations': organisations_schema.dump(organisations).data}
            }
            return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def put(self, organisation_id):
        put_data = request.get_json()
        country_code = put_data.get('country_code')
        default_disbursement = put_data.get('default_disbursement')
        minimum_vendor_payout_withdrawal = put_data.get('minimum_vendor_payout_withdrawal')
        require_transfer_card = put_data.get('require_transfer_card')
        default_lat = put_data.get('default_lat')
        default_lng = put_data.get('default_lng')
        account_types = put_data.get('account_types', [])
        card_shard_distance = put_data.get('card_shard_distance') # Kilometers
        timezone = put_data.get('timezone')

        for at in account_types:
            if at not in ASSIGNABLE_TIERS.keys():
                raise Exception(f'{at} not an assignable role')
        
        if organisation_id is None:
            return make_response(jsonify({'message': 'No organisation ID provided'})), 400

        organisation = Organisation.query.get(organisation_id)
        if organisation is None:
            return make_response(jsonify({'message': f'No organisation found for ID: {organisation_id}'})), 404

        if account_types is not None:
            organisation.valid_roles = account_types
        if default_disbursement is not None:
            organisation.default_disbursement = default_disbursement
        if minimum_vendor_payout_withdrawal is not None:
            organisation.minimum_vendor_payout_withdrawal = minimum_vendor_payout_withdrawal
        if country_code is not None:
            organisation.country_code = country_code
        if require_transfer_card is not None:
            organisation.require_transfer_card = require_transfer_card
        if default_lat is not None:
            organisation.default_lat = default_lat
        if default_lng is not None:
            organisation.default_lng = default_lng
        if card_shard_distance is not None: # Distance in KM
            organisation.card_shard_distance = card_shard_distance
        if timezone is not None:
            organisation.timezone = timezone

        response_object = {
            'message': f'Organisation {organisation_id} successfully updated',
            'data': {'organisation': organisation_schema.dump(organisation).data}
        }

        return make_response(jsonify(response_object)), 200

    @show_all
    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def post(self, organisation_id):
        post_data = request.get_json()

        organisation_name = post_data.get('organisation_name')
        custom_welcome_message_key = post_data.get('custom_welcome_message_key')
        timezone = post_data.get('timezone')

        country_code = post_data.get('country_code')
        default_disbursement = post_data.get('default_disbursement')
        minimum_vendor_payout_withdrawal = post_data.get('minimum_vendor_payout_withdrawal')
        require_transfer_card = post_data.get('require_transfer_card')
        default_lat = post_data.get('default_lat')
        default_lng = post_data.get('default_lng')
        account_types = post_data.get('account_types', [])

        token_id = post_data.get('token_id')
        deploy_cic = post_data.get('deploy_cic', False)

        for at in account_types:
            if at not in ASSIGNABLE_TIERS.keys():
                raise Exception(f'{at} not an assignable role')

        if organisation_name is None or country_code is None:
            return make_response(
                jsonify({'message': 'Must provide name and ISO 2 country_code to create organisation.'})), 400

        existing_organisation = Organisation.query.filter_by(name=organisation_name).execution_options(
            show_all=True).first()
        if existing_organisation is not None:
            return make_response(
                jsonify({
                    'message': 'Must be unique name. Organisation already exists for name: {}'.format(
                        organisation_name),
                    'data': {'organisation': organisation_schema.dump(existing_organisation).data}
                })), 400

        try:
            new_organisation = Organisation(
                name=organisation_name,
                custom_welcome_message_key=custom_welcome_message_key,
                timezone=timezone,
                country_code=country_code,
                default_disbursement=default_disbursement,
                minimum_vendor_payout_withdrawal=minimum_vendor_payout_withdrawal,
                require_transfer_card=require_transfer_card,
                default_lat=default_lat,
                default_lng=default_lng,
                valid_roles=account_types
            )
        except Exception as e:
            response_object = {
                'message': str(e),
            }
            return make_response(jsonify(response_object)), 400

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

        if AccessControl.has_exact_role(g.user.roles, 'ADMIN', 'superadmin'):
            g.user.add_user_to_organisation(new_organisation, is_admin=True)

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


class OrganisationConstantsAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def get(self):
        response_object = {
            'message': 'Organisation constants',
            'data': {
                'iso_countries': ISO_COUNTRIES,
                'timezones': list(pendulum.timezones),
                'roles': list(ASSIGNABLE_TIERS.keys())
                }
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
    '/organisation/<int:organisation_id>/users/',
    view_func=OrganisationUserAPI.as_view('organisation_user_view'),
    methods=['PUT'],
)

organisation_blueprint.add_url_rule(
    '/organisation/constants/',
    view_func=OrganisationConstantsAPI.as_view('organisation_constants_view'),
    methods=['GET'],
)
