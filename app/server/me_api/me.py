from flask import g, make_response, jsonify
from flask.views import MethodView

from server.schemas import user_schema
from server.utils.auth import requires_auth, show_all


class MeAPI(MethodView):
    @requires_auth
    @show_all
    def get(self):

        user = g.user

        serialised_data = user_schema.dump(user).data

        # TODO: Create a better way of having multiple dummy transfer accounts for testing
        # import copy
        # new_ta = copy.deepcopy(serialised_data['transfer_accounts'][0])
        # new_ta['id'] = new_ta['id'] + 1
        # new_ta['balance'] = 99999
        # new_ta['token']['id'] = 2
        # new_ta['token']['symbol'] = 'GOOP'
        #
        # serialised_data['transfer_accounts'].append(new_ta)

        response_object = {
            'message': 'Successfully Loaded.',
            'data': {
                'user': serialised_data
            }
        }

        return make_response(jsonify(response_object)), 201