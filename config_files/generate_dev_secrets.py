import glob
import subprocess
import os
import hashlib
import base64
import configparser
from eth_utils import keccak
from web3 import Web3

def add_val(section, key, value):
    try:
        specific_secrets_parser[section]
    except KeyError:
        specific_secrets_parser[section] = {}

    try:
        value = value.decode()
    except AttributeError:
        pass

    try:
        specific_secrets_parser[section][key] = str(value)
    except Exception as e:
        ttt = 4

def rand_hex(hexlen=16):
    return os.urandom(hexlen).hex()

def eth_pk():
    return Web3.toHex(keccak(os.urandom(4096)))

template_path = './blank_templates'
specific_secrets_read_path = os.path.join(template_path, 'specific_secrets_template.ini')
common_secrets_read_path = os.path.join(template_path, 'common_secrets_template.ini')

specific_secrets_write_path = './secret/local_secrets.ini'
common_secrets_write_path = './secret/common_secrets.ini'

print('Generating deployment specific (local) secrets')

specific_secrets_parser = configparser.ConfigParser()
specific_secrets_parser.read(specific_secrets_read_path)

APP = 'APP'
add_val(APP, 'password_pepper', base64.b64encode(os.urandom(32)))
add_val(APP, 'secret_key', rand_hex(32))
add_val(APP, 'ecdsa_secret', rand_hex(32))
add_val(APP, 'basic_auth_username', 'interal_basic_auth')
add_val(APP, 'basic_auth_password', rand_hex())

DATABASE = 'DATABASE'
add_val(DATABASE, 'user', 'postgres')
add_val(DATABASE, 'password', 'password')


# add_val('HEAP', 'id', '')
#
# add_val('TWILIO', 'phone', '')
#
# MESSAGEBIRD = 'MESSAGEBIRD'
# add_val(MESSAGEBIRD, 'key', '')
# add_val(MESSAGEBIRD, 'phone', '')

ETHEREUM = 'ETHEREUM'
add_val(ETHEREUM, 'master_wallet_private_key', eth_pk())
add_val(ETHEREUM, 'owner_private_key', eth_pk())
add_val(ETHEREUM, 'float_private_key', eth_pk())

add_val('SLACK', 'HOST', '')

# AFRICASTALKING = 'AFRICASTALKING'
# add_val(AFRICASTALKING, 'username', '')
# add_val(AFRICASTALKING, 'api_key', '')
# add_val(AFRICASTALKING, 'at_sender_id', '')

GE_MIGRATION = 'GE_MIGRATION'
# add_val(GE_MIGRATION, 'name', '')
# add_val(GE_MIGRATION, 'user', '')
# add_val(GE_MIGRATION, 'host', '')
# add_val(GE_MIGRATION, 'port', '')
# add_val(GE_MIGRATION, 'password', '')
add_val(GE_MIGRATION, 'ge_http_provider', 'http://127.0.0.1:8500')

with open(specific_secrets_write_path, 'w') as f:
    specific_secrets_parser.write(f)

print('Generated reasonable local secrets, please modify as required')
print('~~~~')
print('Generating common secrets')
common_secrets_parser = configparser.ConfigParser()
common_secrets_parser.read(common_secrets_read_path)
with open(common_secrets_write_path, 'w') as f:
    common_secrets_parser.write(f)
print('Generated reasonable common secrets, please modify as required')

