from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
from server import db
from server.models import KycApplication, BankAccount, UploadedDocument
from server.utils.auth import requires_auth
from server.schemas import kyc_application_schema, kyc_application_state_schema
from server.constants import ALLOWED_FILE_EXTENSIONS
from server.utils.amazon_s3 import save_to_s3_from_document, generate_new_filename

kyc_application_blueprint = Blueprint('kyc_application', __name__)


class KycApplicationAPI(MethodView):
    @requires_auth(allowed_roles=['is_subadmin', 'is_admin', 'is_superadmin'])
    def get(self, kyc_application_id):

        # we only support MASTER (ngo) KYC application currently
        business_details = KycApplication.query.filter_by(type='MASTER').first()

        if business_details is None:
            response_object = {
                'message': 'No business verification details found'
            }

            return make_response(jsonify(response_object)), 404

        if g.user.is_superadmin:
            response_object = {
                'message': 'Successfully loaded business verification details',
                'data': {'kyc_application': kyc_application_schema.dump(business_details).data}
            }

            return make_response(jsonify(response_object)), 200

        # displays kyc_status state only.
        response_object = {
            'message': 'Successfully loaded business verification details',
            'data': {'kyc_application': kyc_application_state_schema.dump(business_details).data}
        }

        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles=['is_superadmin'])
    def put(self, kyc_application_id):
        put_data = request.get_json()

        kyc_status = put_data.get('kyc_status')
        first_name = put_data.get('first_name')
        last_name = put_data.get('last_name')
        phone = put_data.get('phone')
        business_legal_name = put_data.get('business_legal_name')
        business_type = put_data.get('business_type')
        tax_id = put_data.get('tax_id')
        website = put_data.get('website')
        date_established = put_data.get('date_established')
        country = put_data.get('country')
        street_address = put_data.get('street_address')
        street_address_2 = put_data.get('street_address_2')
        city = put_data.get('city')
        region = put_data.get('region')
        postal_code = put_data.get('postal_code')
        beneficial_owners = put_data.get('beneficial_owners')

        if kyc_application_id is None:
            response_object = {
                'message': 'Must provide business profile ID'
            }
            return make_response(jsonify(response_object)), 400

        business = KycApplication.query.get(kyc_application_id)

        if not business:
            response_object = {
                'message': 'Business Verification Profile not found'
            }
            return make_response(jsonify(response_object)), 404

        # update business profile
        if kyc_status:
            business.kyc_status = kyc_status
        if first_name:
            business.first_name = first_name
        if last_name:
            business.last_name = last_name
        if phone:
            business.phone = phone
        if business_legal_name:
            business.business_legal_name = business_legal_name
        if business_type:
            business.business_type = business_type
        if tax_id:
            business.tax_id = tax_id
        if website:
            business.website = website
        if date_established:
            business.date_established = date_established
        if country:
            business.country = country
        if street_address:
            business.street_address = street_address
        if street_address_2:
            business.street_address_2 = street_address_2
        if city:
            business.city = city
        if region:
            business.region = region
        if postal_code:
            business.postal_code = postal_code

        if beneficial_owners is not None:
            # filter empty beneficial owners
            beneficial_owners = [owner for owner in beneficial_owners if (owner['full_name'].strip(' ', ) != '')]

        if beneficial_owners:
            business.beneficial_owners = beneficial_owners

        db.session.commit()

        response_object = {
            'message': 'Successfully Updated KYC Application.',
            'data': {
                'kyc_application': kyc_application_schema.dump(business).data
            }
        }

        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles=['is_superadmin'])
    def post(self, kyc_application_id):
        post_data = request.get_json()

        type = post_data.get('type')
        first_name = post_data.get('first_name')
        last_name = post_data.get('last_name')
        phone = post_data.get('phone')
        business_legal_name = post_data.get('business_legal_name')
        business_type = post_data.get('business_type')
        tax_id = post_data.get('tax_id')
        website = post_data.get('website')
        date_established = post_data.get('date_established')
        country = post_data.get('country')
        street_address = post_data.get('street_address')
        street_address_2 = post_data.get('street_address_2')
        city = post_data.get('city')
        region = post_data.get('region')
        postal_code = post_data.get('postal_code')
        beneficial_owners = post_data.get('beneficial_owners')

        # check for existing business based on Legal Name and Tax ID.
        business_details = KycApplication.query.filter_by(business_legal_name=business_legal_name, tax_id=tax_id).first()

        if business_details is not None:
            response_object = {
                'message': 'Business Verification profile already exists for business name: {} and tax ID: {}'.format(business_legal_name, tax_id)
            }

            return make_response(jsonify(response_object)), 400

        if beneficial_owners is not None:
            # filter empty beneficial owners
            beneficial_owners = [owner for owner in beneficial_owners if(owner['full_name'].strip(' ',) != '')]

        if g.user.is_superadmin:
            type = 'MASTER'

        create_business_details = KycApplication(
            type=type,
            first_name=first_name, last_name=last_name,
            phone=phone, business_legal_name=business_legal_name,
            business_type=business_type, tax_id=tax_id,
            website=website, date_established=date_established,
            country=country, street_address=street_address,
            street_address_2=street_address_2, city=city,
            region=region, postal_code=postal_code,
            beneficial_owners=beneficial_owners,
        )

        db.session.add(create_business_details)
        db.session.commit()

        response_object = {
            'message': 'Business Verification profile created',
            'data': {'kyc_application': kyc_application_schema.dump(create_business_details).data}
        }

        return make_response(jsonify(response_object)), 201


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_FILE_EXTENSIONS


class DocumentUploadAPI(MethodView):
    @requires_auth(allowed_roles=['is_superadmin'])
    def post(self):
        reference = None
        kyc_application_id = None

        if 'kyc_application_id' in request.form:
            kyc_application_id = request.form['kyc_application_id']

        if 'document' not in request.files:
            return make_response(jsonify({'message': 'No File'})), 400

        document = request.files['document']
        filename = document.filename

        if kyc_application_id is None:
            return make_response(jsonify({'message': 'You must append documents to a business profile'})), 400

        if filename == '':
            return make_response(jsonify({'message': 'No File'})), 400

        if not allowed_file(filename):
            return make_response(jsonify({'message': 'Must be JPG, JPEG, PNG or PDF'})), 400

        file_type = filename.rsplit('.', 1)[1].lower()
        new_filename = generate_new_filename(filename, file_type)

        saved_document = UploadedDocument.query.filter_by(filename=new_filename).first()

        if saved_document:
            return make_response(jsonify({'message': 'Document already exists'})), 400

        save_to_s3_from_document(document=document, new_filename=new_filename)

        if 'reference' in request.form:
            reference = request.form['reference']

        uploaded_document = UploadedDocument(filename=new_filename, file_type=file_type,
                                             reference=reference, user_filename=filename)
        db.session.add(uploaded_document)

        business_details = KycApplication.query.filter_by(id=kyc_application_id).first()

        # tie document to kyc application
        uploaded_document.kyc_application_id = business_details.id

        db.session.commit()

        response_object = {
            'message': 'Document uploaded',
            'data': {'kyc_application': kyc_application_schema.dump(business_details).data}
        }

        return make_response(jsonify(response_object)), 201


class BankAccountAPI(MethodView):
    @requires_auth(allowed_roles=['is_superadmin'])
    def post(self, bank_account_id):
        post_data = request.get_json()

        kyc_application_id = post_data.get('kyc_application_id')

        bank_country = post_data.get('bank_country')
        routing_number = post_data.get('routing_number')
        account_number = post_data.get('account_number')
        currency = post_data.get('currency')

        if routing_number is None or account_number is None or bank_country is None or currency is None or kyc_application_id is None:
            response_object = {
                'message': 'Need routing_number, account_number, bank_country, currency and business profile id',
            }

            return make_response(jsonify(response_object)), 400

        # can't create a duplicate bank account at present
        bank_account = BankAccount.query.filter_by(routing_number=routing_number, account_number=account_number).first()

        if bank_account:
            response_object = {
                'message': 'Bank account already exists',
            }

            return make_response(jsonify(response_object)), 400

        # create new bank account
        create_bank_account = BankAccount(
            bank_country=bank_country,
            routing_number=routing_number,
            account_number=account_number,
            currency=currency,
        )

        create_bank_account.kyc_application_id = kyc_application_id

        db.session.add(create_bank_account)
        db.session.commit()

        business_profile = KycApplication.query.filter_by(id=kyc_application_id).first()

        response_object = {
            'message': 'Bank account added',
            'data': {'kyc_application': kyc_application_schema.dump(business_profile).data}
        }

        return make_response(jsonify(response_object)), 201

    @requires_auth(allowed_roles=['is_superadmin'])
    def put(self, bank_account_id):

        put_data = request.get_json()

        kyc_application_id = put_data.get('kyc_application_id')

        bank_country = put_data.get('bank_country')
        routing_number = put_data.get('routing_number')
        account_number = put_data.get('account_number')
        currency = put_data.get('currency')

        if bank_account_id is None:
            return make_response(jsonify({'message': 'You need to provide a bank account ID'})), 400

        bank_account = BankAccount.query.filter_by(id=bank_account_id).first()

        if kyc_application_id is None:
            kyc_application_id = bank_account.kyc_application_id

        business_profile = KycApplication.query.filter_by(id=kyc_application_id)

        if business_profile is None:
            return make_response(jsonify({'message': 'You need to provide a provide a valid business profile ID'})), 400

        if bank_account:
            bank_account.kyc_application_id = kyc_application_id
            bank_account.bank_country = bank_country
            bank_account.routing_number = routing_number
            bank_account.account_number = account_number
            bank_account.currency = currency

        db.session.commit()

        response_object = {
            'message': 'Bank account edited',
            'data': {'kyc_application': kyc_application_schema.dump(business_profile).data}
        }

        return make_response(jsonify(response_object)), 200


kyc_application_blueprint.add_url_rule(
    '/kyc_application/',
    view_func=KycApplicationAPI.as_view('kyc_application_view'),
    methods=['GET', 'PUT', 'POST'],
    defaults={'kyc_application_id': None}
)

kyc_application_blueprint.add_url_rule(
    '/kyc_application/<int:kyc_application_id>/',
    view_func=KycApplicationAPI.as_view('single_kyc_application_view'),
    methods=['GET', 'PUT']
)

kyc_application_blueprint.add_url_rule(
    '/document_upload/',
    view_func=DocumentUploadAPI.as_view('document_upload_view'),
    methods=['POST']
)

kyc_application_blueprint.add_url_rule(
    '/bank_account/',
    view_func=BankAccountAPI.as_view('bank_account_view'),
    methods=['POST', 'PUT'],
    defaults={'bank_account_id': None}
)

kyc_application_blueprint.add_url_rule(
    '/bank_account/<int:bank_account_id>/',
    view_func=BankAccountAPI.as_view('single_bank_account_view'),
    methods=['PUT'],
)
