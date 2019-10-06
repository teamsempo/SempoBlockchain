import random, string, datetime, requests, base64
from flask import current_app


class PoliPaymentsError(Exception):
    pass


def generate_poli_host(path=None):
    host = current_app.config['POLIPAYMENTS_HOST'] + path
    return host


def generate_poli_auth():
    data = current_app.config['POLIPAYMENTS_MERCHANT'] + ':' + current_app.config['POLIPAYMENTS_AUTH']
    token = base64.b64encode(str.encode(data))
    return token.decode()


def generate_poli_header():
    headers = {
        "Authorization": "Basic " + generate_poli_auth(),
    }
    return headers


def create_poli_link(amount):
    """
    Generates a unique POLi Link that a user can than be directed to to pay.

    :param amount: int, amount for the payment to be for.
    :return: unique link
    """
    url = generate_poli_host(path='/POLiLink/Create')
    headers = generate_poli_header()

    def random_string(length):
        return ''.join(random.choices(string.ascii_letters, k=length))

    reference = random_string(5) + '-' + random_string(5)

    one_day_in_future = datetime.datetime.now() + datetime.timedelta(days=1)
    expiry = one_day_in_future.strftime("%Y-%m-%d %H:%M:%S")

    data = {
        "LinkType": 0,
        "Amount": amount,
        "CurrencyCode": "AUD",  # default to AUD. todo: handle NZ
        "MerchantData": reference,
        "MerchantReference": reference,
        "ConfirmationEmail": "false",
        "AllowCustomerReference": "false",
        "ViaEmail": "false",
        "RecipientName": "false",
        "LinkExpiry": expiry,
        "RecipientEmail": "false",
    }

    response = requests.post(url=url, headers=headers, data=data)

    result = response.json()  # todo: check formatting & reference is passed back

    # todo: desired Formatting {'poli_link': 'https://poli.to/saf/', 'reference: 'afsd-afds'}

    return result


def get_poli_link_status(poli_link):
    """
    Get the status of a unique POLi link

    :param poli_link: POLi link unique token (at end of link)
    :return: status, i.e. complete, incomplete
    """
    url = generate_poli_host(path='/POLiLink/Status/{}'.format(poli_link))
    headers = generate_poli_header()

    response = requests.get(url=url, headers=headers)

    result = response.json()  # todo: check formatting

    # todo: desired Formatting {'status': 'completed'}

    return result


def get_poli_link_from_token(token):
    """
    Webhook to get the POLi link from the token received

    :param token: received in the webhook API
    :return: POLi Code
    """
    url = generate_poli_host(path='/POLiLink/FromToken?{}'.format(token))
    headers = generate_poli_header()

    response = requests.get(url=url, headers=headers)

    result = response.json()  # todo: check formatting

    # todo: desired format {'poli_link': 'QZZMS'} status code : 200

    return result
