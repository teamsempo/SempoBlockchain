from typing import Dict
import datetime
from math import log10, floor
import base64
from flask import current_app, request
from eth_utils import keccak
from cryptography.fernet import Fernet
import itertools
from decimal import Decimal

last_marker = datetime.datetime.utcnow()

from eth_keys import keys

# Breaks list into chunks of arbitraty size (I.e. [1,2,3,4,5,6,7] -> [[1,2,3],[4,5,6],[7])
# Taken from https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
def chunk_list(iterable, size):
    it = iter(iterable)
    item = list(itertools.islice(it, size))
    while item:
        yield item
        item = list(itertools.islice(it, size))

def get_parsed_arg_list(arg_name: str, to_lower=False) -> list:
    list_string = request.args.get(arg_name)
    if list_string:
        return [x.lower() if to_lower else x for x in list_string.split(",")]
    else:
        return []

def round_to_sig_figs(amount, sig_figs = 2):
    if amount is None:
        return None

    if amount == 0:
        return 0

    return round(amount, -int(floor(log10(abs(amount)))) + (sig_figs - 1))


def round_to_decimals(amount, decimals=2):
    if amount is None:
        return None

    # Add a small amount before round to override rounding half to even
    return round(amount + Decimal(0.000001), decimals)


def rounded_dollars(amount):
    """
    :param amount: money amount in cents (e.g. 2500)
    :return: rounded dollars as 25.00 (if <1000)
    """
    if amount is None:
        return None

    rounded = round_to_decimals(Decimal(amount) / 100)
    if int(rounded) == Decimal(rounded) and int(rounded) > 1000:
        # It's a large whole amount like 1200.00, so return as 1200
        return str(int(rounded))

    return "{:.2f}".format(rounded)


def hex_private_key_to_address(private_key) -> str:

    if isinstance(private_key, str):
        private_key = bytearray.fromhex(private_key.replace('0x', ''))

    return keys.PrivateKey(private_key).public_key.to_checksum_address()


def elapsed_time(print_statement = None):
    global last_marker
    now = datetime.datetime.utcnow()
    elapsed = now - last_marker
    print('~~~Elapsed time is: {}~~~'.format(elapsed))
    if print_statement:
        print('(At {})'.format(print_statement))
    last_marker = now


def decrypt_string(encryped_string):

    fernet_encryption_key = base64.b64encode(keccak(text=current_app.config['SECRET_KEY']))
    cipher_suite = Fernet(fernet_encryption_key)

    return cipher_suite.decrypt(encryped_string.encode('utf-8')).decode('utf-8')

def encrypt_string(raw_string):

    fernet_encryption_key = base64.b64encode(keccak(text=current_app.config['SECRET_KEY']))
    cipher_suite = Fernet(fernet_encryption_key)

    return cipher_suite.encrypt(raw_string.encode('utf-8')).decode('utf-8')


def attach_host(response: Dict) -> Dict:
    response['host_url'] = current_app.config['APP_HOST']

    return response