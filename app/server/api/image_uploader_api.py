from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db
from server.models import UploadedImage
from server.schemas import uploaded_image_schema
from server.utils.auth import requires_auth
from server.utils.amazon_s3 import save_to_s3_from_image_object, generate_new_filename

image_uploader_blueprint = Blueprint('image_uploader', __name__)

class ImageUploader(MethodView):

    @requires_auth
    def post(self):

        if 'image' not in request.files:
            return jsonify({'message': 'No image'}), 400

        image = request.files['image']

        image_type = request.args.get('imageType')
        transfer_id = request.args.get('transferId')

        original_filename = image.filename

        new_filename = generate_new_filename(original_filename, image_type)

        url = save_to_s3_from_image_object(image_object=image, new_filename=new_filename)

        uploaded_image = UploadedImage(filename=new_filename, image_type=image_type)

        if transfer_id:
            uploaded_image.credit_transfer_id = transfer_id

        db.session.add(uploaded_image)
        db.session.commit()

        response_object = {
            'data': {
                'uploaded_image': uploaded_image_schema.dump(uploaded_image).data
            }
        }

        return make_response(jsonify(response_object)), 201


image_uploader_blueprint.add_url_rule(
    '/image/',
    view_func=ImageUploader.as_view('image_uploader'),
    methods=['POST']
)