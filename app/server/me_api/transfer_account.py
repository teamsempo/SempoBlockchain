from flask import g, make_response, jsonify, request
from flask.views import MethodView

from server.schemas import me_transfer_accounts_schema
from server.utils.auth import requires_auth


class MeTransferAccountAPI(MethodView):
    @requires_auth
    def get(self):

        transfer_accounts = g.user.transfer_accounts

        serialised = me_transfer_accounts_schema.dump(transfer_accounts).data

        response_object = {
            'message': 'Successfully Loaded.',
            'data': {
                'transfer_accounts': serialised,
            }
        }

        return make_response(jsonify(response_object)), 201
