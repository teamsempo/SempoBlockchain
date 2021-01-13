from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
from openpyxl import load_workbook

from server.constants import ALLOWED_SPREADSHEET_EXTENSIONS, SPREADSHEET_UPLOAD_REQUESTED_ATTRIBUTES
from server import db
from server.utils.auth import requires_auth
from server.utils import user as UserUtils

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_SPREADSHEET_EXTENSIONS


dataset_blueprint = Blueprint('dataset', __name__)

class SpreadsheetUploadAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):

        if 'spreadsheet' not in request.files:

            return make_response(jsonify({'message': 'No File'})), 400

        spreadsheet = request.files['spreadsheet']

        if spreadsheet.filename == '':
            return make_response(jsonify({'message': 'No File'})), 400

        if not allowed_file(spreadsheet.filename):
            return make_response(jsonify({'message': 'Must be XSLX or CSV'})), 400

        worksheet = load_workbook(spreadsheet).active

        data_dict = {}
        for i, row in enumerate(worksheet.rows):
            row_dict = {}
            for j, cell in enumerate(row):
                row_dict[j] = cell.value

            data_dict[i] = row_dict

        column_firstrows = {v: k for k, v in data_dict[0].items()}

        reponse_object = {
            'table_data': data_dict,
            'column_firstrows': column_firstrows,
            'requested_attributes':  SPREADSHEET_UPLOAD_REQUESTED_ATTRIBUTES
        }

        return make_response(jsonify(reponse_object)), 200

class DatasetAPI(MethodView):

    def add_diagnostic(self, diagnostic):
        print(diagnostic)
        self.diagnostics.append(diagnostic)

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):
        # get the post data
        post_data = request.get_json()

        is_vendor = post_data.get('isVendor', False)

        header_postions = post_data.get('headerPositions')

        self.diagnostics = []

        for datarow in post_data.get('data'):


            attribute_dict = {}

            contains_anything = False
            for key, header_label in header_postions.items():

                attribute = datarow.get(key)

                if attribute:
                    contains_anything = True
                    attribute_dict[header_label] = attribute

            if contains_anything:
                item_response_object, response_code = UserUtils.proccess_create_or_modify_user_request(
                    attribute_dict, allow_existing_user_modify=True
                )

                self.diagnostics.append((item_response_object.get('message'), response_code))

                if response_code == 200:
                    db.session.commit()
                else:
                    db.session.flush()

        response_object = {
            'status': 'success',
            'message': 'Successfully Saved.',
            'diagnostics': self.diagnostics
        }

        return make_response(jsonify(response_object)), 201


# add Rules for API Endpoints
dataset_blueprint.add_url_rule(
    '/spreadsheet/upload/',
    view_func=SpreadsheetUploadAPI.as_view('spreadsheet_view'),
    methods=['POST']
)

dataset_blueprint.add_url_rule(
    '/dataset/',
    view_func=DatasetAPI.as_view('dataset_view'),
    methods=['POST', 'GET']
)