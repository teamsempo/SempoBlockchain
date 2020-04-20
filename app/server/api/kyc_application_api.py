import sentry_sdk
from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
from server import db
from server.models.bank_account import BankAccount
from server.models.kyc_application import KycApplication
from server.models.upload import UploadedResource
from server.models.user import User
from server.utils.auth import requires_auth
from server.utils.access_control import AccessControl
from server.schemas import kyc_application_schema, kyc_application_state_schema
from server.constants import ALLOWED_FILE_EXTENSIONS
from server.utils.amazon_s3 import save_to_s3_from_document, generate_new_filename, save_to_s3_from_image_base64
from server.utils.slack_controller import post_verification_message

kyc_application_blueprint = Blueprint('kyc_application', __name__)

supported_countries = ['AU', 'TO', 'VU', 'NZ']
supported_documents = {'AU': ['Passport', 'DrivingLicence'], 'TO': ['Passport', 'DrivingLicence', 'CustomerIdentificationCard', 'GovernmentID', 'GovernmentSuperannuationID', 'StudentUniversityID'], 'VU': ['Passport', 'DrivingLicence'], 'NZ': ['Passport', 'DrivingLicence', 'IdentityCard']}


# TODO: Refactor KYC api/models/utils once more insight on business needs
""""
The whole KYC API should go through a refactor to unify Mobile and Web. 
Currently they are fairly segregated, but through the same API making it hard to reason through logic.

 - TODO: Refactor logic into a utils file, so that Kobo and other APIs can create/edit KYC objects
 - TODO: Refactor the "core" logic onto KYC Application model class
 - TODO: Refactor mobile document upload to use same handlers as Web
 - TODO: Refactor supported countries and documents to be unified on web and mobile.
 - TODO: Refactor KYC models so that kyc_actions use helper functions to set/get state on relevant objects 
    (i.e. bank accounts, documents)
"""""


def handle_kyc_documents(data=None,document_country=None,document_type=None,kyc_details=None):
    for (key, value) in data.items():
        if set([key]).intersection(set(['document_front_base64', 'document_back_base64', 'selfie_base64'])) and value is not None:
            try:
                new_filename = generate_new_filename(original_filename="{}-{}.jpg".format(key, document_country), file_type='jpg')
                save_to_s3_from_image_base64(image_base64=value, new_filename=new_filename)
                uploaded_document = UploadedResource(filename=new_filename, reference=document_type,
                                                     user_filename=key)
                db.session.add(uploaded_document)
                # tie document to kyc application
                uploaded_document.kyc_application_id = kyc_details.id
            except Exception as e:
                print(e)
                sentry_sdk.capture_exception(e)
                pass


class KycApplicationAPI(MethodView):
    @requires_auth
    def get(self, kyc_application_id):

        user_id = request.args.get('user_id')

        trulioo_countries = request.args.get('trulioo_countries', None)
        trulioo_documents = request.args.get('trulioo_documents', None)
        country = request.args.get('country', None)

        if trulioo_countries:
            trulioo_countries = supported_countries
            return make_response(jsonify({'message': 'Trulioo Countries', 'data': {'kyc_application': {'trulioo_countries': trulioo_countries}}})), 200

        if trulioo_documents:
            trulioo_documents = {country: supported_documents[country]}
            return make_response(jsonify({'message': 'Trulioo Countries', 'data': {'kyc_application': {'trulioo_documents': trulioo_documents}}})), 200

        if AccessControl.has_suffient_role(g.user.roles, {'ADMIN': 'subadmin'}):
            if user_id:
                # user account KYC
                kyc_details = KycApplication.query.filter_by(user_id=user_id).first()
            else:
                # main organisation KYC
                kyc_details = KycApplication.query.filter_by(organisation_id=g.active_organisation.id).first()

            if kyc_details is None:
                response_object = {
                    'message': 'No business verification details found'
                }

                return make_response(jsonify(response_object)), 404

            if user_id and AccessControl.has_suffient_role(g.user.roles, {'ADMIN': 'admin'}):
                response_object = {
                    'message': 'Successfully loaded business verification details',
                    'data': {'kyc_application': kyc_application_schema.dump(kyc_details).data}
                }

                return make_response(jsonify(response_object)), 200

        else:
            # must be an individual (mobile) user account
            kyc_details = KycApplication.query.filter_by(user_id=g.user.id).first()
            if kyc_details is None:
                return make_response(jsonify({'message': 'No KYC object found for user.', 'data': {'kyc_application': {}}}))

        # displays kyc_status and kyc_actions state only.
        response_object = {
            'message': 'Loaded KYC details',
            'data': {'kyc_application': kyc_application_state_schema.dump(kyc_details).data}
        }

        return make_response(jsonify(response_object)), 200

    @requires_auth
    def put(self, kyc_application_id):
        put_data = request.get_json()

        is_mobile = put_data.get('is_mobile')

        document_type = put_data.get('document_type')
        document_country = put_data.get('document_country')
        document_front_base64 = put_data.get('document_front_base64')  # image
        document_back_base64 = put_data.get('document_back_base64')  # image
        selfie_base64 = put_data.get('selfie_base64')  # image

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

        kyc_details = None

        if is_mobile:
            if document_type is None or document_country is None or document_front_base64 is None or selfie_base64 is None:
                return make_response(jsonify({'message': 'Must provide correct parameters'})), 400

            kyc_details = KycApplication.query.filter_by(user_id=g.user.id).first()
            if kyc_details is None:
                return make_response(jsonify({'message': 'No KYC object found'})), 400

            kyc_details.kyc_attempts = kyc_details.kyc_attempts + 1

            if kyc_details.kyc_attempts > 2:
                # only allow two attempts
                kyc_details.kyc_status = 'REJECTED'
                db.session.commit()
                return make_response(jsonify({'message': 'KYC attempts exceeded. Contact Support.'})), 400

            kyc_details.kyc_status = 'PENDING'

            # handle document upload to s3
            handle_kyc_documents(data=put_data, document_country=document_country, document_type=document_type,
                                 kyc_details=kyc_details)

            # Post verification message to slack
            post_verification_message(user=g.user)

            response_object = {
                'message': 'Successfully Updated KYC Application.',
                'data': {
                    'kyc_application': kyc_application_schema.dump(kyc_details).data
                }
            }

            return make_response(jsonify(response_object)), 200

        if not is_mobile:
            if kyc_application_id is None:
                response_object = {
                    'message': 'Must provide business profile ID'
                }
                return make_response(jsonify(response_object)), 400

            kyc_details = KycApplication.query.get(kyc_application_id)

            if not kyc_details:
                response_object = {
                    'message': 'Business Verification Profile not found'
                }
                return make_response(jsonify(response_object)), 404

            if kyc_details.organisation_id and AccessControl.has_suffient_role(g.user.roles, {'ADMIN': 'superadmin'}) is not True:
                return make_response(jsonify({'message': 'Must be a superadmin to edit admin org KYC object'})), 401

            if AccessControl.has_suffient_role(g.user.roles, {'ADMIN': 'subadmin'}) is not True:
                return make_response(jsonify({'message': 'Must be a subadmin to edit any KYC object'})), 401

            # update business profile
            if kyc_status:
                kyc_details.kyc_status = kyc_status
            if first_name:
                kyc_details.first_name = first_name
            if last_name:
                kyc_details.last_name = last_name
            if phone:
                kyc_details.phone = phone
            if business_legal_name:
                kyc_details.business_legal_name = business_legal_name
            if business_type:
                kyc_details.business_type = business_type
            if tax_id:
                kyc_details.tax_id = tax_id
            if website:
                kyc_details.website = website
            if date_established:
                kyc_details.date_established = date_established
            if country:
                kyc_details.country = country
            if street_address:
                kyc_details.street_address = street_address
            if street_address_2:
                kyc_details.street_address_2 = street_address_2
            if city:
                kyc_details.city = city
            if region:
                kyc_details.region = region
            if postal_code:
                kyc_details.postal_code = postal_code

            if beneficial_owners is not None:
                # filter empty beneficial owners
                beneficial_owners = [owner for owner in beneficial_owners if (owner['full_name'].strip(' ', ) != '')]

            if beneficial_owners:
                kyc_details.beneficial_owners = beneficial_owners

            if kyc_status == 'PENDING':
                # Final web submission. Post verification message to slack
                post_verification_message(user=kyc_details.user)

        response_object = {
            'message': 'Successfully Updated KYC Application.',
            'data': {
                'kyc_application': kyc_application_schema.dump(kyc_details).data
            }
        }

        return make_response(jsonify(response_object)), 200

    @requires_auth
    def post(self, kyc_application_id):
        post_data = request.get_json()

        is_mobile = post_data.get('is_mobile')
        user_id = post_data.get('user_id')  # should only be defined when an admin is adding user KYC data (not their own)

        type = post_data.get('account_type', 'BUSINESS').upper()
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

        document_type = post_data.get('document_type')
        document_country = post_data.get('document_country')
        document_front_base64 = post_data.get('document_front_base64')  # image
        document_back_base64 = post_data.get('document_back_base64')  # image
        selfie_base64 = post_data.get('selfie_base64')  # image

        if is_mobile or user_id:

            # creation logic is handled after kyc object creation.
            kyc_details = KycApplication.query.filter_by(user_id=user_id or g.user.id).first()
            if kyc_details is not None:
                return make_response(jsonify({'message': 'KYC details already exist'})), 400

            if not user_id and (document_type is None or document_country is None or document_front_base64 is None or selfie_base64 is None):
                return make_response(jsonify({'message': 'Must provide correct parameters'})), 400

        if not is_mobile and type == 'BUSINESS':

            if user_id and AccessControl.has_suffient_role(g.user.roles, {'ADMIN': 'subadmin'}) is not True:
                return make_response(jsonify({'message': 'Must be superadmin to create any KYC profile'})), 401

            elif AccessControl.has_suffient_role(g.user.roles, {'ADMIN': 'superadmin'}) is not True:
                return make_response(jsonify({'message': 'Must be superadmin to create org business KYC profile'})), 401

            # check for existing business based on Legal Name and Tax ID.
            business_details = KycApplication.query.filter_by(business_legal_name=business_legal_name, tax_id=tax_id).first()

            if business_details is not None:
                response_object = {
                    'message': 'Business Verification profile already exists for business name: {} and tax ID: {}'.format(business_legal_name, tax_id)
                }

                return make_response(jsonify(response_object)), 400

        if not is_mobile and (business_legal_name is None and tax_id is None) and not user_id:
            # not mobile, not a org profile, thus user_id cannot be None
            return make_response(jsonify({'message': 'Must provide a user id to create a user KYC profile'})), 400

        if beneficial_owners is not None:
            # filter empty beneficial owners
            beneficial_owners = [owner for owner in beneficial_owners if(owner['full_name'].strip(' ',) != '')]

        create_kyc_application = KycApplication(
            type=type, user=g.user,
            first_name=first_name or g.user.first_name, last_name=last_name or g.user.last_name,
            phone=phone or g.user.phone, business_legal_name=business_legal_name,
            business_type=business_type, tax_id=tax_id,
            website=website, date_established=date_established,
            country=country or document_country, street_address=street_address,
            street_address_2=street_address_2, city=city,
            region=region, postal_code=postal_code,
            beneficial_owners=beneficial_owners,
        )

        if user_id:
            user = User.query.get(user_id)
            create_kyc_application.user = user or g.user

        if not is_mobile:
            # not mobile
            if not user_id and type == 'BUSINESS':
                # not a admin applying for another user
                # ngo organisation
                create_kyc_application.organisation = g.active_organisation
            else:
                # admin applying for another user (individual or business)
                create_kyc_application.kyc_status = 'INCOMPLETE'

        db.session.add(create_kyc_application)
        db.session.flush()  # need this to create an ID

        if is_mobile:
            # handle document upload to s3
            handle_kyc_documents(data=post_data, document_country=document_country, document_type=document_type,
                                 kyc_details=create_kyc_application)

            # Post verification message to slack
            post_verification_message(user=g.user)

        response_object = {
            'message': 'KYC Application created',
            'data': {'kyc_application': kyc_application_state_schema.dump(create_kyc_application).data}
        }

        return make_response(jsonify(response_object)), 201


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_FILE_EXTENSIONS


class DocumentUploadAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'subadmin'})
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

        business_details = KycApplication.query.filter_by(id=kyc_application_id).first()

        if not business_details:
            return make_response(jsonify({'message': 'Cannot find kyc for id {}'.format(kyc_application_id)})), 404

        if business_details.organisation_id and AccessControl.has_suffient_role(g.user.roles, {'ADMIN': 'superadmin'}) is not True:
            return make_response(jsonify({'message': 'Must be a superadmin to edit admin org KYC object'})), 401

        if filename == '':
            return make_response(jsonify({'message': 'No File'})), 400

        if not allowed_file(filename):
            return make_response(jsonify({'message': 'Must be JPG, JPEG, PNG or PDF'})), 400

        file_type = filename.rsplit('.', 1)[1].lower()
        new_filename = generate_new_filename(filename, file_type)

        saved_document = UploadedResource.query.filter_by(filename=new_filename).first()

        if saved_document:
            return make_response(jsonify({'message': 'Document already exists'})), 400

        save_to_s3_from_document(document=document, new_filename=new_filename)

        if 'reference' in request.form:
            reference = request.form['reference']

        uploaded_document = UploadedResource(filename=new_filename, file_type=file_type,
                                             reference=reference, user_filename=filename)
        db.session.add(uploaded_document)

        # tie document to kyc application
        uploaded_document.kyc_application_id = business_details.id

        response_object = {
            'message': 'Document uploaded',
            'data': {'kyc_application': kyc_application_schema.dump(business_details).data}
        }

        return make_response(jsonify(response_object)), 201


class BankAccountAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'subadmin'})
    def post(self, bank_account_id):
        post_data = request.get_json()

        kyc_application_id = post_data.get('kyc_application_id')

        bank_country = post_data.get('bank_country')
        routing_number = post_data.get('routing_number')
        account_number = post_data.get('account_number')
        currency = post_data.get('currency')

        business_details = KycApplication.query.filter_by(id=kyc_application_id).first()

        if not business_details:
            return make_response(jsonify({'message': 'Cannot find kyc for id {}'.format(kyc_application_id)})), 404

        if business_details.organisation_id and AccessControl.has_suffient_role(g.user.roles,
                                                                                {'ADMIN': 'superadmin'}) is not True:
            return make_response(jsonify({'message': 'Must be a superadmin to edit admin org KYC object'})), 401

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

        create_bank_account.kyc_application = business_details

        db.session.add(create_bank_account)

        response_object = {
            'message': 'Bank account added',
            'data': {'kyc_application': kyc_application_schema.dump(business_details).data}
        }

        return make_response(jsonify(response_object)), 201

    @requires_auth(allowed_roles={'ADMIN': 'subadmin'})
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

        business_details = KycApplication.query.filter_by(id=kyc_application_id).first()

        if not business_details:
            return make_response(jsonify({'message': 'Cannot find kyc for id {}'.format(kyc_application_id)})), 404

        if business_details.organisation_id and AccessControl.has_suffient_role(g.user.roles,
                                                                                {'ADMIN': 'superadmin'}) is not True:
            return make_response(jsonify({'message': 'Must be a superadmin to edit admin org KYC object'})), 401

        if bank_account:
            bank_account.kyc_application_id = kyc_application_id
            bank_account.bank_country = bank_country
            bank_account.routing_number = routing_number
            bank_account.account_number = account_number
            bank_account.currency = currency

        response_object = {
            'message': 'Bank account edited',
            'data': {'kyc_application': kyc_application_schema.dump(business_details).data}
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
