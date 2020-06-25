import os
import uuid
from typing import cast

from eth_utils import keccak
from eth_keys import keys
from web3 import Web3

from sempo_types import UUID

def keypair():

    pk = keccak(os.urandom(4096))
    address = keys.PrivateKey(pk).public_key.to_checksum_address()

    return {
        'pk': Web3.toHex(pk),
        'address': address
    }

deterministic_address_1 = '0x468F90c5a236130E5D51260A2A5Bfde834C694b6'
deterministic_address_2 = '0x68D3ce90D84B4DD8936908Afd4079797057996bB'

def str_uuid() -> UUID:
    return cast(UUID, str(uuid.uuid4()))