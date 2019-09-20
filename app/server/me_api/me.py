from flask import request, g, make_response, jsonify
from flask.views import MethodView
from sqlalchemy import or_

from server.models import CreditTransfer, paginate_query
from server.schemas import user_schema, old_user_schema
from server.utils.auth import requires_auth, show_all, AccessControl


class MeAPI(MethodView):
    @requires_auth
    @show_all
    def get(self):

        version = request.args.get('version', 1)

        if str(version) == '2':
            user = g.user

            responseObject = {
                'message': 'Successfully Loaded.',
                'data': {
                    'user': user_schema.dump(user).data,
                }
            }

            return make_response(jsonify(responseObject)), 201


        user = g.user

        if AccessControl.has_suffient_role(user.roles, {'ADMIN': 'subadmin', 'VENDOR': 'supervendor'}):
            # admins and supervendors see all transfers for that transfer account
            transfer_account = user.transfer_account

            transfers_query = CreditTransfer.query.filter(
                or_(CreditTransfer.recipient_transfer_account_id == transfer_account.id,
                    CreditTransfer.sender_transfer_account_id == transfer_account.id))

        else:
            # other users only see transfers involving themselves
            transfers_query = CreditTransfer.query.filter(
                or_(CreditTransfer.recipient_user_id == user.id,
                    CreditTransfer.sender_user_id == user.id))

        transfers, total_items, total_pages = paginate_query(transfers_query, CreditTransfer)

        responseObject = {
            'message': 'Successfully Loaded.',
            'items': total_items,
            'pages': total_pages,
            'data': {
                'user': old_user_schema.dump(user).data,
                # 'credit_transfers': transfer_list,
            }
        }

        return make_response(jsonify(responseObject)), 201