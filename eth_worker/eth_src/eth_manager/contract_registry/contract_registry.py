import json
import os
from eth_utils import to_checksum_address

class ContractRegistry(object):

    def get_compiled_contract(self, contract_name):

        data  = self.get_contract_json(contract_name)

        bytecode = data['bytecode']
        abi = data['abi']

        return self.w3.eth.contract(abi=abi, bytecode=bytecode)

    def get_contract_json(self, contract_name):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path, f'./stripped_compiled_contracts/{contract_name}.json')
        with open(file_path) as json_file:
            return json.load(json_file)

    def register_abi(self, name, abi):
        self.contract_abis[name] = abi

    def register_contract(self, contract_address, abi):
        checksum_address = to_checksum_address(contract_address)

        contract = self.w3.eth.contract(address=checksum_address, abi=abi)

        self.contracts_by_address[contract_address] = contract

        return contract

    def get_contract_by_address(self, contract_address, abi_type=None):
        contract = self.contracts_by_address.get(contract_address)

        if not contract and not abi_type:
            raise Exception('Contract not found for address: {}'.format(contract_address))

        if not contract:
            abi = self.contract_abis.get(abi_type)

            if abi is None:
                try:
                    data = self.get_contract_json(abi_type)
                    abi = data.get('abi')
                except FileNotFoundError:
                    abi = None

            if abi is None:
                raise Exception('ABI not found for type: {}'.format(abi_type))

            contract = self.register_contract(contract_address, abi)

        return contract

    def get_contract_function(self, contract_address, function_name, abi_type=None):
        contract = self.get_contract_by_address(contract_address, abi_type)
        return getattr(contract.functions, function_name)

    def __init__(self, w3):

        self.w3 = w3
        self.contracts_by_address = {}
        self.contract_abis = {}
        self.compiled_contracts = {}
