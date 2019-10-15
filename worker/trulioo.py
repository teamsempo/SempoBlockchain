import requests, config
from requests.auth import HTTPBasicAuth


def trulioo_auth():
    return HTTPBasicAuth(config.TRULIOO_USER, config.TRULIOO_PASS)


#test auth
# requests.get(config.TRULIOO_HOST + '/connection/v1/testauthentication', auth=trulioo_auth())

def trulioo_verify(data):

    response = requests.post(config.TRULIOO_HOST + '/verifications/v1/verify/', auth=trulioo_auth(), json=data)

    return response.json()


def trulioo_task(task):
    kyc_application_id = task.get('kyc_application_id')
    body = task.get('body')  # pre-formatted request body

    if not body:
        return {'status': 'fail'}

    response = trulioo_verify(body)

    response['kyc_application_id'] = kyc_application_id

    return response
