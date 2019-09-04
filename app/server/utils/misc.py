import datetime
import base64
import re
from flask import current_app
from eth_utils import keccak
from cryptography.fernet import Fernet
from server import models

last_marker = datetime.datetime.utcnow()

from eth_keys import keys

def hex_private_key_to_address(hex_private_key: str) -> str:
    bytes_key = bytearray.fromhex(hex_private_key.strip('0x'))
    return keys.PrivateKey(bytes_key).public_key.to_checksum_address()


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



class AttributeDictProccessor(object):

    def force_attribute_dict_keys_to_lowercase(self):
        return dict(zip(map(str.lower, self.attribute_dict.keys()), self.attribute_dict.values()))

    def strip_kobo_preslashes(self):
        self.attribute_dict = dict(zip(map(lambda key: key[self._return_index_of_slash_or_neg1(key) + 1:], self.attribute_dict.keys()),
                        self.attribute_dict.values()))

    def insert_settings_from_databse(self, settings_list):
        for setting in settings_list:
            if setting not in self.attribute_dict:
                stored_setting = models.Settings.query.filter_by(name=setting).first()

                if stored_setting is not None:
                    self.attribute_dict[setting] = stored_setting.value

    def attempt_to_truthy_dict_values(self):
        self.attribute_dict = dict(zip(self.attribute_dict.keys(), map(self._convert_yes_no_string_to_bool, self.attribute_dict.values())))

    def strip_weirdspace_characters(self):
        """
        'weirdspace' (tm nick 2019) characters are tabs, newlines and returns
        """

        self.attribute_dict = dict(zip(map(self._remove_whitespace_from_string, self.attribute_dict.keys()),
                        map(self._remove_whitespace_from_string, self.attribute_dict.values())))

    def _return_index_of_slash_or_neg1(self, string):
        try:
            return str(string).index("/")
        except ValueError:
            return -1

    def _convert_yes_no_string_to_bool(self, test_string):
        if str(test_string).lower() in ["yes", "true", "1"]:
            return True
        elif str(test_string).lower() in ["no", "false", "0"]:
            return False
        else:
            return test_string

    def _remove_whitespace_from_string(self, maybe_string):
        if isinstance(maybe_string, str):
            return re.sub(r'[\t\n\r]', '', maybe_string)
        else:
            return maybe_string

    def __init__(self, attribute_dict: dict):
        self.attribute_dict = attribute_dict