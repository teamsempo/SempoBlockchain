from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.utils.auth import requires_auth
from server.utils import user as UserUtils
from server.utils.misc import AttributeDictProccessor
from server.constants import CREATE_USER_SETTINGS


user_kobo_blueprint = Blueprint('user_kobo', __name__)


class UserKoboAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'}, allowed_basic_auth_types=('external'))
    def post(self, user_id):
        post_data = request.get_json()

        # Data supplied to the API via integrations such as KoboToolbox can be messy, so clean the data first
        dict_processor = AttributeDictProccessor(post_data)
        dict_processor.force_attribute_dict_keys_to_lowercase()
        dict_processor.strip_kobo_preslashes()
        dict_processor.attempt_to_truthy_dict_values()
        dict_processor.strip_weirdspace_characters()
        dict_processor.insert_settings_from_databse(CREATE_USER_SETTINGS)
        post_data = dict_processor.attribute_dict

        post_data = UserUtils.extract_kobo_custom_attributes(post_data)

        response_object, response_code = UserUtils.proccess_create_or_modify_user_request(
            post_data,
            organisation=g.user.get_active_organisation()
        )

        if response_code == 200:
            db.session.commit()

        return make_response(jsonify(response_object)), response_code


# add Rules for API Endpoints

user_kobo_blueprint.add_url_rule(
    '/kobo/user',
    view_func=UserKoboAPI.as_view('user_kobo_view'),
    methods=['POST'],
    defaults={'user_id': None}
)
