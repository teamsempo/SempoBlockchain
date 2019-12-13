from flask import g, make_response, jsonify
from flask.views import MethodView

from server.schemas import me_organisation_schema
from server.utils.auth import requires_auth


class MeOrganisationAPI(MethodView):
    @requires_auth
    def get(self):

        organisation = g.user.default_organisation

        serialised_data = me_organisation_schema.dump(organisation).data

        response_object = {
            'message': 'Successfully Loaded.',
            'data': {
                'organisation': serialised_data
            }
        }

        return make_response(jsonify(response_object)), 201
