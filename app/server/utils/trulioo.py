import requests, config
from requests.auth import HTTPBasicAuth
from server.utils.phone import send_generic_message
from server.models.user import User

def get_callback_url():
    return config.APP_HOST + '/api/trulioo_async/'


def trulioo_auth():
    return HTTPBasicAuth(config.TRULIOO_USER, config.TRULIOO_PASS)


def get_trulioo_countries():
    response = requests.get(config.TRULIOO_HOST + '/configuration/v1/countrycodes/Identity%20Verification/',
                            auth=trulioo_auth())
    return response.json()


def get_trulioo_country_documents(country):
    response = requests.get(config.TRULIOO_HOST + '/configuration/v1/documentTypes/' + country,
                            auth=trulioo_auth())
    return response.json()


def get_trulioo_consents(country):
    response = requests.get(config.TRULIOO_HOST + '/configuration/v1/consents/Identity Verification/' + country,
                            auth=trulioo_auth())

    return response.json()


def get_trulioo_transaction(transaction_id):
    response = requests.get(config.TRULIOO_HOST + '/verifications/v1/transactionrecord/' + transaction_id,
                            auth=trulioo_auth())

    return response.json()


def handle_trulioo_response(response=None, kyc_application=None):
    # Record.RecordStatus = match.  means successful verification
    record_errors = None
    document_errors = None
    phone = None

    user = User.query.get(kyc_application.user_id)
    if user is not None:
        phone = user.phone

    authenticity_reasons = ["DatacomparisonTooLow", "ExpiredDocument", "ValidationFailure", "LivePhotoNOMatch", "UnclassifiedDocument", "SuspiciousDocument"]

    status = response['Record']['RecordStatus']
    if status == 'match':
        kyc_application.kyc_status = 'VERIFIED'

        if phone is not None:
            send_generic_message(to_phone=phone, message='Hooray! Your identity has been successfully verified and Sempo account limits lifted.')

    if status == 'nomatch' or status == 'missing':
        # currently only handle 1 datasource (i.e. document)

        errors = response['Record']['DatasourceResults'][0]['Errors']
        if len(response['Record']['DatasourceResults'][0]['Errors']) > 0:
            record_errors = [error['Code'] for error in errors]

            if '3100' or '3101' in record_errors:
                # Blurry or Glare Image, retry, send text
                kyc_application.kyc_status = 'INCOMPLETE'
                kyc_application.kyc_actions = ['retry']

                if phone is not None:
                    send_generic_message(to_phone=phone,
                                         message="Unfortunately, we couldn't verify your identity with the documents provided. Please open the Sempo app to retry.")

        for key in response['Record']['DatasourceResults'][0]['AppendedFields']:
            if key['FieldName'] == 'AuthenticityReasons':
                document_errors = key['Data']

                if document_errors in authenticity_reasons:
                    if document_errors == 'SuspiciousDocument':
                        # document has been rejected, contact support, send text.
                        kyc_application.kyc_status = 'REJECTED'
                        kyc_application.kyc_actions = ['support']

                        if phone is not None:
                            send_generic_message(to_phone=phone,
                                                 message="Unfortunately, we couldn't verify your identity with the documents provided. Please contact Sempo customer support in the app.")
                    else:
                        # document has been rejected, try again, send text.
                        kyc_application.kyc_status = 'INCOMPLETE'
                        kyc_application.kyc_actions = ['retry']

                        if phone is not None:
                            send_generic_message(to_phone=phone,
                                                 message="Unfortunately, we couldn't verify your identity with the documents provided. Please open the Sempo app to retry.")

    # return verification status, document Authenticity Reasons and OCR appended fields
    return {
        'status': status,
        'record_errors': record_errors,
        'document_errors': document_errors,
    }
