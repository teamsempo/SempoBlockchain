import hmac, hashlib, time, requests, json
from flask import current_app


class WyreError(Exception):
    pass


def handle_wyre_error(response):
    if response.status_code != 200 or 201:
        result = json.loads(response.content)
        if result['message'] is not None:
            wyre_error = result['message']
            raise WyreError(wyre_error)


def generate_wyre_signature(url, body):
    if body is None:
        signature = str(url).encode('utf-8')
    else:
        to_encode = str(url) + str(body)
        signature = to_encode.encode('utf-8')

    return hmac.new(current_app.config['WYRE_SECRET_KEY'].encode('utf-8'), signature, hashlib.sha256).hexdigest()


def generate_wyre_header(url, body):
    headers = {
        "X-Api-Key": current_app.config['WYRE_PUBLIC_KEY'],
        "X-Api-Signature": generate_wyre_signature(url=url, body=body),
    }
    return headers


def generate_url(version=None, *args):
    milli_time = str(int(round(time.time() * 1000)))

    host = current_app.config['WYRE_HOST']  # defaults to version 3
    if version == 'v2':
        host = current_app.config['WYRE_HOST_V2']
    if version == 'v3':
        host = current_app.config['WYRE_HOST']

    return host + ''.join(args) + '?timestamp=' + milli_time


def get_account(wyre_id):
    url = generate_url('v3', 'accounts/', wyre_id)
    body = None
    headers = generate_wyre_header(url=url, body=body)

    response = requests.get(url=url, headers=headers, data=body)
    handle_wyre_error(response)
    return json.loads(response.content)


def list_payment_methods():
    url = generate_url('v2', 'paymentMethods')
    body = None
    headers = generate_wyre_header(url=url, body=body)

    response = requests.get(url=url, headers=headers, data=body)
    handle_wyre_error(response)
    return json.loads(response.content)


def create_transfer(source_amount, source_account, source_currency, dest_amount, dest_address, dest_currency, message, auto_confirm='true', preview=False, include_fees=False):
    callback_url = current_app.config['APP_HOST'] + '/api/wyre_webhook/'
    url = generate_url('v2', 'transfers')
    body = None

    if source_amount and dest_amount is None:
        raise WyreError('Must include a source amount or dest_amount')

    if (source_account or source_currency or dest_address or dest_currency) is None:
        raise WyreError('Must include source_account, source_currency, dest_address and dest_currency')

    if source_amount:
        body = {
            'sourceAmount': source_amount,
            'source': source_account,  # wyre SRN
            'sourceCurrency': source_currency,
            'dest': dest_address,  # eth address
            'destCurrency': dest_currency,  # DAI
            'message': message,
            "autoConfirm": auto_confirm,
            "preview": preview,
            "amountIncludesFees": include_fees,
            "notifyUrl": callback_url
        }
    if dest_amount:
        body = {
            'source': source_account,
            'sourceCurrency': source_currency,
            'destAmount': dest_amount,
            'dest': dest_address,
            'destCurrency': dest_currency,
            'message': message,
            "autoConfirm": auto_confirm,
            "preview": preview,
            "amountIncludesFees": include_fees,
            "notifyUrl": callback_url
        }

    headers = generate_wyre_header(url=url, body=json.dumps(body))

    response = requests.post(url=url, headers=headers, data=json.dumps(body))
    handle_wyre_error(response)
    return json.loads(response.content)


def get_exchange_rates():
    url = generate_url('v3', 'rates')
    body = None
    headers = generate_wyre_header(url=url, body=body)

    response = requests.get(url=url, headers=headers, data=body)
    handle_wyre_error(response)
    return json.loads(response.content)


def get_transfer(transfer_id):
    url = generate_url('v3', 'transfers/', transfer_id)
    body = None
    headers = generate_wyre_header(url=url, body=body)

    response = requests.get(url=url, headers=headers, data=body)
    handle_wyre_error(response)
    return json.loads(response.content)


def get_transfer_history():
    url = generate_url('v3', 'transfers')
    body = None
    headers = generate_wyre_header(url=url, body=body)

    response = requests.get(url=url, headers=headers, data=body)
    return json.loads(response.content)
