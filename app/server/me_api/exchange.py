from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server.utils.auth import requires_auth, show_all
from server.models.token import Token
from server.models.exchange import Exchange
from server.schemas import me_exchange_schema, me_exchanges_schema
from server import db

class ExchangeAPI(MethodView):

    @requires_auth
    def get(self, exchange_id):

        if exchange_id:
            exchange = Exchange.query.get(exchange_id)

            response_object = {
                'message': 'success',
                'data': {
                    'exchange': me_exchange_schema.dump(exchange).data
                }
            }

            return make_response(jsonify(response_object)), 201

        exchanges = Exchange.query.all()

        response_object = {
            'message': 'success',
            'data': {
                'exchanges': me_exchanges_schema.dump(exchanges).data
            }
        }

        return make_response(jsonify(response_object)), 201


    @requires_auth
    @show_all
    def post(self, exchange_id):
        """
        Exchange Entry Point Method
        Method: POST

        :param from_token_id: the ID of the token being exchanged from
        :param to_token_id: the ID of the token being exchanged to
        :param from_amount: the amount of the token being exchanged from

        :return: status of exchange, and serialised exchange object if successful
        """

        post_data = request.get_json()

        user = g.user

        from_token_id = post_data.get('from_token_id')
        to_token_id = post_data.get('to_token_id')

        from_amount = post_data.get('from_amount')
        to_desired_amount = post_data.get('to_desired_amount')

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

        if from_amount and to_desired_amount:
            response_object = {
                'message': 'Must not specify both from amount and to amount',
            }
            return make_response(jsonify(response_object)), 400
        elif from_amount:
            try:
                exchange = Exchange()

                exchange.exchange_from_amount(
                    user=user,
                    from_token=from_token,
                    to_token=to_token,
                    from_amount=from_amount
                )

            except Exception as e:

                db.session.commit()

                response_object = {
                    'message': str(e),
                }
                return make_response(jsonify(response_object)), 400

        elif to_desired_amount:

            # TODO: Test this
            try:
                exchange = Exchange()

                exchange.exchange_to_desired_amount(
                    user=user,
                    from_token=from_token,
                    to_token=to_token,
                    to_desired_amount=to_desired_amount
                )
            except Exception as e:

                db.session.commit()

                response_object = {
                    'message': str(e),
                }
                return make_response(jsonify(response_object)), 400

        else:

            response_object = {
                'message': 'Must specify either from amount or to amount',
            }
            return make_response(jsonify(response_object)), 400

        response_object = {
            'message': 'Exchange Successful',
            'data': {
                'exchange': me_exchange_schema.dump(exchange).data
            }
        }

        return make_response(jsonify(response_object)), 200
