from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server.models.token import Token


class ExchangeAPI(MethodView):

    """
        Exchange Entry Point Method
        Method: POST

        :param from_token_id: the ID of the token being exchanged from
        :param to_token_id: the ID of the token being exchanged to
        :param from_amount: the amount of the token being exchanged from

        :return: status of exchange, and serialised exchange object if successful
    """
    def post(self):
        post_data = request.get_json()

        user = g.user

        from_token_id = post_data.get('from_token_id')
        to_token_id = post_data.get('to_token_id')

        from_amount = post_data.get('from_amount')
        to_desired_amount = post_data.get('to_desired_amount')

        if not from_amount and not to_desired_amount:
            response_object = {
                'message': 'Must specify either from amount or to amount',
            }
            return make_response(jsonify(response_object)), 400

        if from_amount and to_desired_amount:
            response_object = {
                'message': 'Must not specify both from amount and to amount',
            }
            return make_response(jsonify(response_object)), 400

        from_token = Token.query.get(from_token_id)
        to_token = Token.query.get(to_token_id)

        if not from_token:
            response_object = {
                'message': f'From token not found for ID {from_token_id}',
            }
            return make_response(jsonify(response_object)), 400

        if not to_token:
            response_object = {
                'message': f'To token not found for ID {to_token_id}',
            }
            return make_response(jsonify(response_object)), 400



        response_object = {
            'message': 'Transfer Successful',
            'data': {
                'exchange': 'foo',
            }
        }
        return make_response(jsonify(response_object)), 201

