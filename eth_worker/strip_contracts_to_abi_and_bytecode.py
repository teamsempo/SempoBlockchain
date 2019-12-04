import glob
import json
import os

for path in glob.glob('/Users/Nick/WebstormProjects/BancorContracts/solidity/build/contracts/*.json'):
    head, filename = os.path.split(path)
    with open(path) as json_file:
        data = json.load(json_file)

        bytecode = data['bytecode']
        abi = data['abi']

        with open(f'./eth_manager/stripped_compiled_contracts/{filename}', 'w') as outfile:
            json.dump({'abi': abi, 'bytecode': bytecode}, outfile)
