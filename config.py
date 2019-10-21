import os, configparser, boto3, hashlib
from botocore.exceptions import EndpointConnectionError
from eth_keys import keys
from eth_utils import keccak

from web3 import Web3

CONFIG_DIR = os.path.abspath(os.path.dirname(__file__))

# ENV_DEPLOYMENT_NAME: dev, 'acmecorp-prod' etc
ENV_DEPLOYMENT_NAME = os.environ.get('DEPLOYMENT_NAME') or 'local'
BUILD_HASH = os.environ.get('GIT_HASH') or 'null'

print('ENV_DEPLOYMENT_NAME: ' + ENV_DEPLOYMENT_NAME)
print('with BUILD_HASH: ' + BUILD_HASH)

CONFIG_FILENAME = "{}_config.ini".format(ENV_DEPLOYMENT_NAME.lower())

common_parser = configparser.ConfigParser()
specific_parser = configparser.ConfigParser()

if os.environ.get('AWS_ACCESS_KEY_ID'):
    print("ATTEMPT LOAD S3 CONFIG (AWS ACCESS KEY FOUND)")
    load_from_s3 = True
elif os.environ.get('SERVER_HAS_S3_AUTH'):
    print("ATTEMPT LOAD S3 CONFIG (SERVER CLAIMS TO HAVE S3 AUTH)")
    load_from_s3 = True
else:
    print("ATTEMPT LOAD LOCAL CONFIG")
    load_from_s3 = False

if load_from_s3:
    # Load config from S3 Bucket

    if os.environ.get('AWS_ACCESS_KEY_ID'):
        # S3 Auth is set via access keys
        if not os.environ.get('AWS_SECRET_ACCESS_KEY'):
            raise Exception("Missing AWS_SECRET_ACCESS_KEY")
        session = boto3.Session(
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )
    else:
        # The server itself has S3 Auth
        session = boto3.Session()

    client = session.client('s3')

    SECRET_BUCKET = "ctp-prod-secrets"
    FORCE_SSL = True

    specific_obj = client.get_object(Bucket=SECRET_BUCKET, Key=CONFIG_FILENAME)
    specific_read_result = specific_obj['Body'].read().decode('utf-8')
    specific_parser.read_string(specific_read_result)

    common_obj = client.get_object(Bucket=SECRET_BUCKET, Key='common_config.ini')
    common_read_result = common_obj['Body'].read().decode('utf-8')
    common_parser.read_string(common_read_result)

else:
    # Load config from local

    # This occurs in local environments
    folder_common_path = os.path.join(CONFIG_DIR, 'config_files/common_config.ini')
    folder_specific_path = os.path.join(CONFIG_DIR, 'config_files/' + CONFIG_FILENAME)

    # This occurs in docker environments, where the config folder is copied and unpacked to the parent directory
    # We can't avoid unpacking the config folder due to docker stupidness around conditional file copying
    raw_common_path = os.path.join(CONFIG_DIR, 'common_config.ini')
    raw_specific_path = os.path.join(CONFIG_DIR, CONFIG_FILENAME)

    common_path = folder_common_path if os.path.isfile(folder_common_path) else raw_common_path
    specific_path = folder_specific_path if os.path.isfile(folder_specific_path) else raw_specific_path

    if not os.path.isfile(common_path):
        raise Exception("Missing Common Config File")

    if not os.path.isfile(specific_path):
        raise Exception("Missing Config File: {}".format(CONFIG_FILENAME))

    common_parser.read(common_path)
    specific_parser.read(specific_path)

DEPLOYMENT_NAME = specific_parser['APP']['DEPLOYMENT_NAME']

# Check that the deployment name specified by the env matches the one in the config file
if ENV_DEPLOYMENT_NAME.lower() != DEPLOYMENT_NAME.lower():
    raise RuntimeError('deployment name in env ({}) does not match that in config ({}), aborting'.format(ENV_DEPLOYMENT_NAME.lower(),
                                                                                            DEPLOYMENT_NAME.lower()))


IS_TEST = specific_parser['APP'].getboolean('IS_TEST', False)
IS_PRODUCTION = specific_parser['APP'].getboolean('IS_PRODUCTION')
if IS_PRODUCTION is None:
    raise KeyError("IS_PRODUCTION key not found")

PROGRAM_NAME        = specific_parser['APP']['PROGRAM_NAME']
CURRENCY_NAME       = specific_parser['APP']['CURRENCY_NAME']
CURRENCY_DECIMALS   = int(specific_parser['APP']['CURRENCY_DECIMALS'])
STARTING_BALANCE    = int(specific_parser['APP']['STARTING_BALANCE'])
DEFAULT_COUNTRY     = specific_parser['APP']['DEFAULT_COUNTRY']
DEFAULT_LAT         = float(specific_parser['APP']['DEFAULT_LAT'])
DEFAULT_LNG         = float(specific_parser['APP']['DEFAULT_LNG'])
BENEFICIARY_TERM    = specific_parser['APP']['BENEFICIARY_TERM']
BENEFICIARY_TERM_PLURAL = specific_parser['APP']['BENEFICIARY_TERM_PLURAL']
CHATBOT_REQUIRE_PIN = specific_parser['APP'].getboolean('CHATBOT_REQUIRE_PIN')
DEFAULT_FEEDBACK_QUESTIONS = list(specific_parser['APP']['DEFAULT_FEEDBACK_QUESTIONS'].split(','))
FEEDBACK_TRIGGERED_WHEN_BALANCE_BELOW = int(specific_parser['APP']['FEEDBACK_TRIGGERED_WHEN_BALANCE_BELOW'])
FEEDBACK_TRIGGERED_WHEN_TRANSFER_COUNT_ABOVE = int(specific_parser['APP']['FEEDBACK_TRIGGERED_WHEN_TRANSFER_COUNT_ABOVE'])
REQUIRE_TARGETING_SURVEY = specific_parser['APP'].getboolean('REQUIRE_TARGETING_SURVEY')

CASHOUT_INCENTIVE_PERCENT = float(specific_parser['APP'].get('CASHOUT_INCENTIVE_PERCENT', 0))
AUTO_APPROVE_TRANSFER_ACCOUNTS = specific_parser['APP'].getboolean('AUTO_APPROVE_TRANSFER_ACCOUNTS', False)
MAXIMUM_CUSTOM_INITIAL_DISBURSEMENT = int(specific_parser['APP'].get('MAXIMUM_CUSTOM_INITIAL_DISBURSEMENT', 0))
ONBOARDING_SMS = specific_parser['APP'].getboolean('ONBOARDING_SMS', False)
TFA_REQUIRED_ROLES = specific_parser['APP']['TFA_REQUIRED_ROLES'].split(',')
MOBILE_VERSION = specific_parser['APP']['MOBILE_VERSION']

SECRET_KEY          = specific_parser['APP']['SECRET_KEY'] + DEPLOYMENT_NAME
ECDSA_SECRET        = hashlib.sha256(specific_parser['APP']['ECDSA_SECRET'].encode()).digest()[0:24]
APP_HOST            = specific_parser['APP']['APP_HOST']

TOKEN_EXPIRATION =  60 * 60 * 24 * 1 # Day

INTERNAL_AUTH_USERNAME = common_parser['APP']['BASIC_AUTH_USERNAME'] + '_' + DEPLOYMENT_NAME
INTERNAL_AUTH_PASSWORD = common_parser['APP']['BASIC_AUTH_PASSWORD']

EXTERNAL_AUTH_USERNAME = 'admin_auth_' + DEPLOYMENT_NAME
EXTERNAL_AUTH_PASSWORD = hashlib.sha256(SECRET_KEY.encode()).hexdigest()[0:8]

BASIC_AUTH_CREDENTIALS = {
    INTERNAL_AUTH_USERNAME: (INTERNAL_AUTH_PASSWORD, 'internal'),
    EXTERNAL_AUTH_USERNAME: (EXTERNAL_AUTH_PASSWORD, 'external')
}

REDIS_URL = 'redis://' + specific_parser['REDIS']['URI']

DATABASE_USER = specific_parser['DATABASE'].get('user') \
                or '{}_{}'.format(common_parser['DATABASE']['user'],DEPLOYMENT_NAME.replace("-", "_"))

DATABASE_HOST = specific_parser['DATABASE']['host']

DATABASE_NAME = specific_parser['DATABASE'].get('database') \
                or common_parser['DATABASE']['database']

ETH_DATABASE_NAME = specific_parser['DATABASE'].get('eth_database') \
                    or common_parser['DATABASE']['eth_database']

ETH_DATABASE_HOST = specific_parser['DATABASE'].get('eth_host') or DATABASE_HOST

def get_database_uri(name, host, censored=True):
    return 'postgresql://{}:{}@{}:{}/{}'.format(DATABASE_USER,
                                                '*******' if censored else specific_parser['DATABASE']['password'],
                                                host,
                                                common_parser['DATABASE']['port'],
                                                name)


SQLALCHEMY_DATABASE_URI = get_database_uri(DATABASE_NAME, DATABASE_HOST, censored=False)
CENSORED_URI            = get_database_uri(DATABASE_NAME, DATABASE_HOST, censored=True)

ETH_DATABASE_URI     = get_database_uri(ETH_DATABASE_NAME, ETH_DATABASE_HOST, censored=False)
CENSORED_ETH_URI     = get_database_uri(ETH_DATABASE_NAME, ETH_DATABASE_HOST, censored=True)

print('Main database URI: ' + CENSORED_URI)
print('Eth database URI: ' + CENSORED_ETH_URI)


SQLALCHEMY_TRACK_MODIFICATIONS = False

AWS_SES_KEY_ID = common_parser['AWS']['ses_key_id']
AWS_SES_SECRET = common_parser['AWS']['ses_secret']

if IS_PRODUCTION:
    SENTRY_SERVER_DSN = common_parser['SENTRY']['server_dsn']
    SENTRY_REACT_DSN = common_parser['SENTRY']['react_dsn']
else:
    SENTRY_SERVER_DSN = ''
    SENTRY_REACT_DSN = ''


GOOGLE_GEOCODE_KEY = common_parser['GOOGLE']['geocode_key']
CHROMEDRIVER_LOCATION = specific_parser['GOOGLE']['chromedriver_location']
GOOGLE_ANALYTICS_ID = common_parser['GOOGLE']['google_analytics_id']

HEAP_ANALYTICS_ID = specific_parser['HEAP']['id']

MAPBOX_TOKEN = common_parser['MAPBOX']['token']

PUSHER_APP_ID   = common_parser['PUSHER']['app_id']
PUSHER_KEY      = common_parser['PUSHER']['key']
PUSHER_SECRET   = common_parser['PUSHER']['secret']
PUSHER_CLUSTER  = common_parser['PUSHER']['cluser']
PUSHER_ENV_CHANNEL = common_parser['PUSHER']['environment_channel'] + '-' + DEPLOYMENT_NAME
PUSHER_SUPERADMIN_ENV_CHANNEL = common_parser['PUSHER']['superadmin_environment_channel'] + '-' + DEPLOYMENT_NAME

TWILIO_SID   = common_parser['TWILIO']['sid']
TWILIO_TOKEN = common_parser['TWILIO']['token']
TWILIO_PHONE = specific_parser['TWILIO']['phone']

MESSAGEBIRD_KEY = specific_parser['MESSAGEBIRD']['key']
MESSAGEBIRD_PHONE = specific_parser['MESSAGEBIRD']['phone']

try:
    from ecdsa import SigningKey, NIST192p
    ECDSA_SIGNING_KEY = SigningKey.from_string(ECDSA_SECRET, curve=NIST192p)
    ECDSA_PUBLIC = '04' + ECDSA_SIGNING_KEY.get_verifying_key().to_string().hex()
except ImportError:
    pass

# https://ropsten.infura.io/9CAC3Lb5OjaoecQIpPNP
# https://kovan.infura.io/9CAC3Lb5OjaoecQIpPNP

ETH_HTTP_PROVIDER       = specific_parser['ETHEREUM']['http_provider']
ETH_WEBSOCKET_PROVIDER  = specific_parser['ETHEREUM'].get('websocket_provider')
ETH_CHAIN_ID            = specific_parser['ETHEREUM']['chain_id'] or 1
ETH_CHAIN_NAME          = {1: '', 3: 'Ropsten', 42: 'Kovan'}.get(int(ETH_CHAIN_ID), '')
ETH_OWNER_ADDRESS       = specific_parser['ETHEREUM']['owner_address']
ETH_OWNER_PRIVATE_KEY   = specific_parser['ETHEREUM']['owner_private_key']
ETH_CONTRACT_VERSION    = specific_parser['ETHEREUM']['contract_version']
ETH_GAS_PRICE           = int(specific_parser['ETHEREUM']['gas_price_gwei'] or 0)
ETH_GAS_LIMIT           = int(specific_parser['ETHEREUM']['gas_limit'] or 0)
ETH_TARGET_TRANSACTION_TIME = int(specific_parser['ETHEREUM']['target_transaction_time'] or 120)
ETH_GAS_PRICE_PROVIDER  = specific_parser['ETHEREUM']['gas_price_provider']
ETH_CONTRACT_NAME       = 'SempoCredit{}_v{}'.format(DEPLOYMENT_NAME,str(ETH_CONTRACT_VERSION))

ETH_CHECK_TRANSACTION_BASE_TIME = 20
ETH_CHECK_TRANSACTION_RETRIES = int(specific_parser['ETHEREUM']['check_transaction_retries'])
ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT = sum(
    [ETH_CHECK_TRANSACTION_BASE_TIME * 2 ** i for i in range(1,ETH_CHECK_TRANSACTION_RETRIES + 1)]
)

INTERNAL_TO_TOKEN_RATIO = float(specific_parser['ETHEREUM'].get('internal_to_token_ratio', 1))
FORCE_ETH_DISBURSEMENT_AMOUNT = float(specific_parser['ETHEREUM'].get('force_eth_disbursement_amount', 0))

unchecksummed_withdraw_to_address     = specific_parser['ETHEREUM'].get('withdraw_to_address')
if unchecksummed_withdraw_to_address:
    WITHDRAW_TO_ADDRESS = Web3.toChecksumAddress(unchecksummed_withdraw_to_address)
else:
    WITHDRAW_TO_ADDRESS = None

master_wallet_private_key = keccak(text=SECRET_KEY + DEPLOYMENT_NAME)
MASTER_WALLET_PRIVATE_KEY = master_wallet_private_key.hex()
MASTER_WALLET_ADDRESS = keys.PrivateKey(master_wallet_private_key).public_key.to_checksum_address()
print(f'Master Wallet address: {MASTER_WALLET_ADDRESS}')

SYSTEM_WALLET_TARGET_BALANCE = int(specific_parser['ETHEREUM'].get('system_wallet_target_balance', 0))
SYSTEM_WALLET_TOPUP_THRESHOLD = int(specific_parser['ETHEREUM'].get('system_wallet_topup_threshold', 0))

ETH_CONTRACT_TYPE       = specific_parser['ETHEREUM'].get('contract_type', 'standard').lower()
ETH_CONTRACT_ADDRESS    = specific_parser['ETHEREUM'].get('contract_address')
USING_EXTERNAL_ERC20    = ETH_CONTRACT_TYPE != 'mintable'

if specific_parser['ETHEREUM'].get('dai_contract_address'):
    # support of old config file syntax
    ETH_CONTRACT_ADDRESS = specific_parser['ETHEREUM'].get('dai_contract_address')

IS_USING_BITCOIN = False

RESERVE_TOKEN_ADDRESS = specific_parser['ETHEREUM'].get('reserve_token_address')
EXCHANGE_CONTRACT_ADDRESS = specific_parser['ETHEREUM'].get('exchange_contract_address')

FACEBOOK_TOKEN = common_parser['FACEBOOK']['token']
FACEBOOK_VERIFY_TOKEN = common_parser['FACEBOOK']['verify_token']

AP_IS_ACTIVE             = specific_parser['ASSEMBLYPAYMENTS'].getboolean('ap_is_active')
ASSEMBLYPAYMENTS_HOST = specific_parser['ASSEMBLYPAYMENTS']['host']
ASSEMBLYPAYMENTS_EMAIL = common_parser['ASSEMBLYPAYMENTS']['email']
ASSEMBLYPAYMENTS_KEY = common_parser['ASSEMBLYPAYMENTS']['key']

WYRE_PUBLIC_KEY = common_parser['WYRE']['public_key']
WYRE_SECRET_KEY = common_parser['WYRE']['secret_key']
WYRE_HOST = specific_parser['WYRE']['host']
WYRE_HOST_V2 = specific_parser['WYRE']['host_v2']

IPIFY_API_KEY = common_parser['IPIFY']['api_key']

INTERCOM_ANDROID_SECRET = common_parser['INTERCOM']['android_secret']

SLACK_HOST      = specific_parser['SLACK']['host']
SLACK_API_TOKEN = common_parser['SLACK']['token']
SLACK_SECRET    = common_parser['SLACK']['secret']

try:
    NAMESCAN_KEY    = common_parser['NAMESCAN']['key']
except KeyError:
    NAMESCAN_KEY = None
