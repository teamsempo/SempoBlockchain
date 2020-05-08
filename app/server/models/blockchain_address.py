import os, base64
from eth_utils import keccak
from flask import current_app
from cryptography.fernet import Fernet
from sqlalchemy.ext.hybrid import hybrid_property
from web3 import Web3

from server.utils.misc import hex_private_key_to_address
from server.constants import (
    ALLOWED_BLOCKCHAIN_ADDRESS_TYPES
)
from server import db
from server.models.utils import ModelBase, OneOrgBase


class BlockchainAddress(OneOrgBase, ModelBase):
    __tablename__ = 'blockchain_address'

    address             = db.Column(db.String())
    encoded_private_key = db.Column(db.String())

    # Either "MASTER", "TRANSFER_ACCOUNT" or "EXTERNAL"
    type = db.Column(db.String())

    transfer_account_id = db.Column(db.Integer, db.ForeignKey("transfer_account.id"))

    credit_sends = db.relationship('CreditTransfer', backref='sender_blockchain_address',
                                   lazy='dynamic', foreign_keys='CreditTransfer.sender_blockchain_address_id')

    credit_receives = db.relationship('CreditTransfer', backref='recipient_blockchain_address',
                                      lazy='dynamic', foreign_keys='CreditTransfer.recipient_blockchain_address_id')

    @hybrid_property
    def decrypted_private_key(self):

        fernet_encryption_key = base64.b64encode(keccak(text=current_app.config['SECRET_KEY']))
        cipher_suite = Fernet(fernet_encryption_key)

        return cipher_suite.decrypt(self.encoded_private_key.encode('utf-8')).decode('utf-8')

    def encrypt_private_key(self, unencoded_private_key):

        fernet_encryption_key = base64.b64encode(keccak(text=current_app.config['SECRET_KEY']))
        cipher_suite = Fernet(fernet_encryption_key)

        return cipher_suite.encrypt(unencoded_private_key.encode('utf-8')).decode('utf-8')

    def calculate_address(self, private_key):
        self.address = hex_private_key_to_address(private_key)

    def allowed_types(self):
        return ALLOWED_BLOCKCHAIN_ADDRESS_TYPES

    def __init__(self, type, blockchain_address=None):

        if type not in self.allowed_types():
            raise Exception("type {} not one of {}".format(type, self.allowed_types()))

        self.type = type

        if blockchain_address:
            self.address = blockchain_address

        if self.type == "TRANSFER_ACCOUNT" and not blockchain_address:

            hex_private_key = Web3.toHex(keccak(os.urandom(4096)))

            self.encoded_private_key = self.encrypt_private_key(hex_private_key)

            self.calculate_address(hex_private_key)
