from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server.utils.attribute_preprocessor import standard_user_preprocess
from server import db
from server.utils.auth import requires_auth
from server.utils import user as UserUtils
from server.constants import CREATE_USER_SETTINGS


user_kobo_blueprint = Blueprint('user_kobo', __name__)

class UserKoboAPI(MethodView):
    @requires_auth(allowed_basic_auth_types=('external',))
    def post(self, user_id):
        data = request.get_json()

        # Data supplied to the API via integrations such as KoboToolbox can be messy, so clean the data first
        data = standard_user_preprocess(data, CREATE_USER_SETTINGS)

        response_object, response_code = UserUtils.proccess_create_or_modify_user_request(
            data,
            organisation=g.active_organisation
        )

        if response_code == 200:
            db.session.commit()

        return make_response(jsonify(response_object)), response_code


# add Rules for API Endpoints

user_kobo_blueprint.add_url_rule(
    '/kobo/user/',
    view_func=UserKoboAPI.as_view('user_kobo_view'),
    methods=['POST'],
    defaults={'user_id': None}
)
