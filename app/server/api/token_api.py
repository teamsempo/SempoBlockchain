from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db
from server.utils.auth import requires_auth
from server.models.token import Token
from server.schemas import token_schema, tokens_schema

token_blueprint = Blueprint('token', __name__)

class TokenAPI(MethodView):

    @requires_auth(allowed_basic_auth_types=['internal'])
    def get(self):
        tokens = Token.query.all()

        response_object = {
            'message': 'success',
            'data': {
                'tokens': tokens_schema.dump(tokens).data
            }
        }

        return make_response(jsonify(response_object)), 200


    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self):
        post_data = request.get_json()

        address = post_data['address']
        name = post_data['name']
        symbol = post_data['symbol']

        token = Token.query.filter_by(address=address).first()

        if token:
            response_object = {
                'message': 'Token already exists',
                'data': {
                    'token': token_schema.dump(token).data
                }
            }

            return make_response(jsonify(response_object)), 400

        token = Token(address=address, name=name, symbol=symbol)

        db.session.add(token)
        db.session.commit()

        response_object = {
            'message': 'success',
            'data': {
                'token': {
                    'id': token.id
                }
            }
        }

        return make_response(jsonify(response_object)), 201

token_blueprint.add_url_rule(
    '/token/',
    view_func=TokenAPI.as_view('token_view'),
    methods=['POST', 'GET']
)