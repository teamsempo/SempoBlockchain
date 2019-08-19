import datetime
import base64
from ethereum import utils
from flask import current_app
from cryptography.fernet import Fernet

last_marker = datetime.datetime.utcnow()

def elapsed_time(print_statement = None):
    global last_marker
    now = datetime.datetime.utcnow()
    elapsed = now - last_marker
    print('~~~Elapsed time is: {}~~~'.format(elapsed))
    if print_statement:
        print('(At {})'.format(print_statement))
    last_marker = now


def decrypt_string(encryped_string):

    fernet_encryption_key = base64.b64encode(utils.sha3(current_app.config['SECRET_KEY']))
    cipher_suite = Fernet(fernet_encryption_key)

    return cipher_suite.decrypt(encryped_string.encode('utf-8')).decode('utf-8')

def encrypt_string(raw_string):

    fernet_encryption_key = base64.b64encode(utils.sha3(current_app.config['SECRET_KEY']))
    cipher_suite = Fernet(fernet_encryption_key)

    return cipher_suite.encrypt(raw_string.encode('utf-8')).decode('utf-8')

