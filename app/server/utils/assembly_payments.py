import base64
import requests
import random, string
from flask import current_app

cca2tocca3 = {"AF":"AFG","AX":"ALA","AL":"ALB","DZ":"DZA","AS":"ASM","AD":"AND","AO":"AGO","AI":"AIA","AQ":"ATA","AG":"ATG","AR":"ARG","AM":"ARM","AW":"ABW","SH":"SHN","AU":"AUS","AT":"AUT","AZ":"AZE","BS":"BHS","BH":"BHR","BD":"BGD","BB":"BRB","BY":"BLR","BE":"BEL","BZ":"BLZ","BJ":"BEN","BM":"BMU","BT":"BTN","BO":"BOL","BQ":"BES","BA":"BIH","BW":"BWA","BV":"BVT","BR":"BRA","IO":"IOT","VG":"VGB","BN":"BRN","BG":"BGR","BF":"BFA","BI":"BDI","KH":"KHM","CM":"CMR","CA":"CAN","CV":"CPV","KY":"CYM","CF":"CAF","TD":"TCD","CL":"CHL","CN":"CHN","CX":"CXR","CC":"CCK","CO":"COL","KM":"COM","CG":"COG","CD":"COD","CK":"COK","CR":"CRI","HR":"HRV","CU":"CUB","CW":"CUW","CY":"CYP","CZ":"CZE","DK":"DNK","DJ":"DJI","DM":"DMA","DO":"DOM","EC":"ECU","EG":"EGY","SV":"SLV","GQ":"GNQ","ER":"ERI","EE":"EST","ET":"ETH","FK":"FLK","FO":"FRO","FJ":"FJI","FI":"FIN","FR":"FRA","GF":"GUF","PF":"PYF","TF":"ATF","GA":"GAB","GM":"GMB","GE":"GEO","DE":"DEU","GH":"GHA","GI":"GIB","GR":"GRC","GL":"GRL","GD":"GRD","GP":"GLP","GU":"GUM","GT":"GTM","GG":"GGY","GN":"GIN","GW":"GNB","GY":"GUY","HT":"HTI","HM":"HMD","VA":"VAT","HN":"HND","HK":"HKG","HU":"HUN","IS":"ISL","IN":"IND","ID":"IDN","CI":"CIV","IR":"IRN","IQ":"IRQ","IE":"IRL","IM":"IMN","IL":"ISR","IT":"ITA","JM":"JAM","JP":"JPN","JE":"JEY","JO":"JOR","KZ":"KAZ","KE":"KEN","KI":"KIR","KW":"KWT","KG":"KGZ","LA":"LAO","LV":"LVA","LB":"LBN","LS":"LSO","LR":"LBR","LY":"LBY","LI":"LIE","LT":"LTU","LU":"LUX","MO":"MAC","MK":"MKD","MG":"MDG","MW":"MWI","MY":"MYS","MV":"MDV","ML":"MLI","MT":"MLT","MH":"MHL","MQ":"MTQ","MR":"MRT","MU":"MUS","YT":"MYT","MX":"MEX","FM":"FSM","MD":"MDA","MC":"MCO","MN":"MNG","ME":"MNE","MS":"MSR","MA":"MAR","MZ":"MOZ","MM":"MMR","NA":"NAM","NR":"NRU","NP":"NPL","NL":"NLD","NC":"NCL","NZ":"NZL","NI":"NIC","NE":"NER","NG":"NGA","NU":"NIU","NF":"NFK","KP":"PRK","MP":"MNP","NO":"NOR","OM":"OMN","PK":"PAK","PW":"PLW","PS":"PSE","PA":"PAN","PG":"PNG","PY":"PRY","PE":"PER","PH":"PHL","PN":"PCN","PL":"POL","PT":"PRT","PR":"PRI","QA":"QAT","XK":"KOS","RE":"REU","RO":"ROU","RU":"RUS","RW":"RWA","BL":"BLM","KN":"KNA","LC":"LCA","MF":"MAF","PM":"SPM","VC":"VCT","WS":"WSM","SM":"SMR","ST":"STP","SA":"SAU","SN":"SEN","RS":"SRB","SC":"SYC","SL":"SLE","SG":"SGP","SX":"SXM","SK":"SVK","SI":"SVN","SB":"SLB","SO":"SOM","ZA":"ZAF","GS":"SGS","KR":"KOR","SS":"SSD","ES":"ESP","LK":"LKA","SD":"SDN","SR":"SUR","SJ":"SJM","SZ":"SWZ","SE":"SWE","CH":"CHE","SY":"SYR","TW":"TWN","TJ":"TJK","TZ":"TZA","TH":"THA","TL":"TLS","TG":"TGO","TK":"TKL","TO":"TON","TT":"TTO","TN":"TUN","TR":"TUR","TM":"TKM","TC":"TCA","TV":"TUV","UG":"UGA","UA":"UKR","AE":"ARE","GB":"GBR","US":"USA","UM":"UMI","VI":"VIR","UY":"URY","UZ":"UZB","VU":"VUT","VE":"VEN","VN":"VNM","WF":"WLF","EH":"ESH","YE":"YEM","ZM":"ZMB","ZW":"ZWE"}


class UserIdentifierNotFoundError(Exception):
    pass


class AssemblyPaymentsError(Exception):
    pass


def handle_ap_error(response):
    if response.status_code != 200 or 201:
        # todo --- merge dict key && value into str
        result = response.json()
        if result.get('errors') is not None:
            assembly_payments_error = next(iter(result.get('errors').values()))[0]   # get first error message
            raise AssemblyPaymentsError(assembly_payments_error)


def generate_ap_token():
    data = current_app.config['ASSEMBLYPAYMENTS_EMAIL'] + ':' + current_app.config['ASSEMBLYPAYMENTS_KEY']
    token = base64.b64encode(str.encode(data))
    return token.decode()


def generate_ap_header():
    headers = {
        "Authorization": "Basic " + generate_ap_token(),
    }
    return headers


def get_host():
    host = current_app.config['ASSEMBLYPAYMENTS_HOST']
    return host


def create_ap_user(email, mobile, first_name, last_name, dob, government_number, addressline_1, city, state, zip_code, country):
    url = get_host() + 'users'
    headers = generate_ap_header()

    def random_string(length):
        return ''.join(random.choices(string.ascii_letters, k=length))

    ap_id = random_string(5) + '-' + random_string(5) + '-' + random_string(5) + '-' + random_string(5)

    data = {
        "id": ap_id,
        "email": email,
        "mobile": mobile,
        "first_name": first_name,
        "last_name": last_name,
        "dob": dob,
        "government_number": government_number,
        "addressline_1": addressline_1,
        "city": city,
        "state": state,
        "zip": zip_code,
        "country": country,
    }

    response = requests.post(url=url, headers=headers, data=data)

    handle_ap_error(response)

    result = response.json()

    return result


def create_bank_account(user_id, bank_name, account_name, routing_number, account_number, account_type, holder_type, country, payout_currency):
    url = get_host() + 'bank_accounts'
    headers = generate_ap_header()

    if user_id is None:
        raise UserIdentifierNotFoundError('No user id provided')

    data = {
        "user_id": user_id,
        "bank_name": bank_name,
        "account_name": account_name,
        "routing_number": routing_number,
        "account_number": account_number,
        "account_type": account_type,
        "holder_type": holder_type,
        "country": cca2tocca3[country],
        "payout_currency": payout_currency,
    }

    response = requests.post(url=url, headers=headers, data=data)

    handle_ap_error(response)

    result = response.json()

    return result


def create_paypal_account(user_id, paypal_email):
    url = get_host() + 'paypal_accounts'
    headers = generate_ap_header()

    if user_id is None:
        raise UserIdentifierNotFoundError('No user id provided')

    data = {
        "user_id": user_id,
        "paypal_email": paypal_email
    }

    response = requests.post(url=url, headers=headers, data=data)

    handle_ap_error(response)

    result = response.json()

    return result


def set_user_disbursement_account(user_id, account_id):
    url = get_host() + 'users/' + user_id + '/disbursement_account'
    headers = generate_ap_header()

    if user_id is None:
        raise UserIdentifierNotFoundError('No user id provided')

    form = "account_id=" + account_id

    response = requests.patch(url=url, headers=headers, form=form)

    handle_ap_error(response)

    result = response.json()

    return result
