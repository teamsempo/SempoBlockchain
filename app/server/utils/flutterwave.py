from uuid import uuid4
import requests 
import config

FLUTTERWAVE_API_URL = 'https://api.flutterwave.com/v3/'
TRANSFERS_ENDPOINT = 'transfers'

SUPPORTED_COUNTIES = ['UG']

# "MPS" charge type, named after M-Pesa
# Used by them as a generic term for mobile money
CHARGE_TYPES = {
    'UG': 'MPS'
}

MINIMUM_TRANSFER_AMOUNTS = {
    'UG': 1000
}

COUNTRY_CURRENCIES = {
    'UG': 'UGX'
}

def _make_mobile_money_payment(name, phone_number, country, amount):
    if country not in SUPPORTED_COUNTIES:
        raise Exception(
            f"Country {country} not supported. Please use one of the following: {' '.join(SUPPORTED_COUNTIES)}")

    if amount < MINIMUM_TRANSFER_AMOUNTS[country]:
        raise Exception(
            f'Cannot complete payment as transfer does not meet transfer minimum value of {MINIMUM_TRANSFER_AMOUNTS[country]} {COUNTRY_CURRENCIES[country]}')

    url = FLUTTERWAVE_API_URL + TRANSFERS_ENDPOINT

    payload = {
        "account_number": phone_number,
        "account_bank": CHARGE_TYPES[country],
        "narration": "",
        "amount": amount,
        "currency": COUNTRY_CURRENCIES[country],
        "debit_currency": COUNTRY_CURRENCIES[country],
        "reference": str(uuid4()),
        "beneficiary_name": name,
        "destination_branch_code": ""
    }

    resp = requests.post(url=url, data=payload, headers={'Authorization': config.FLUTTEWAVE_SECRET_KEY}).json()
    if resp['status'] == 'error':
        raise Exception(resp['message'])

    if resp['status'] == 'success':
        return True
        
def make_withdrawal(fiat_ramp):
    user = fiat_ramp.credit_transfer.sender_user
    try:
        _make_mobile_money_payment(
            user.first_name + ' ' + user.last_name, 
            user.phone_number,
            user.default_organisation.country_code,
            fiat_ramp.payment_amount
        )

    except Exception as e:
        raise e
