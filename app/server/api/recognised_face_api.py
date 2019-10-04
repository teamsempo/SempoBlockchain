from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db
from server.models.upload import UploadedImage
from server.utils.auth import requires_auth

from sqlalchemy.orm.attributes import flag_modified


recognised_face_blueprint = Blueprint('recognised_face', __name__)

def get_user_from_image_id(image_id):
    matching_image = UploadedImage.query.get(image_id)
    if matching_image and matching_image.user:
        return matching_image.user
    else:
        return None

class RecognisedFaceAPI(MethodView):

    @requires_auth(allowed_basic_auth_types=('internal'))
    def post(self):

        post_data = request.get_json()

        image_id = post_data.get('image_id')
        roll = post_data.get('roll')

        user = get_user_from_image_id(image_id)

        if user is not None:

            # custom_attributes = user.custom_attributes
            #
            # custom_attributes['profile_picture']['roll'] = roll


            user.custom_attributes['profile_picture']['roll'] = roll
            flag_modified(user, "custom_attributes")
            db.session.add(user)
            db.session.commit()

            return make_response(jsonify({'message': 'roll applied'})), 201

        return make_response(jsonify({'message': 'user not found'})), 400

    @requires_auth(allowed_basic_auth_types=('internal'))
    def put(self):

        put_data = request.get_json()

        original_image_id = put_data.get('image_id')
        recognised_faces = put_data.get('recognised_faces')

        original_user = get_user_from_image_id(original_image_id)

        match_list = []

        if not original_user:
            return make_response(jsonify({'message': 'No user found for original image ID'})), 400

        for face in recognised_faces:
            matching_user = get_user_from_image_id(face[0])

            if matching_user:
                profile_picture = matching_user.custom_attributes.get('profile_picture')
                if profile_picture:
                    profile_picture['user_id'] = matching_user.id
                    match_list.append(profile_picture)

        original_user.matched_profile_pictures = match_list

        db.session.commit()

        return make_response(jsonify({'message': 'matches updated'})), 201

recognised_face_blueprint.add_url_rule(
    '/recognised_face/',
    view_func=RecognisedFaceAPI.as_view('recognised_face_view'),
    methods=['POST', 'PUT']
)
