import requests
import config
from time import sleep

def load_account(address, amount_wei):
    from web3 import (
        Web3,
        HTTPProvider
    )

    w3 = Web3(HTTPProvider(config.ETH_HTTP_PROVIDER))

    tx_hash = w3.eth.sendTransaction(
        {'to': address, 'from': w3.eth.accounts[0], 'value': amount_wei})
    return w3.eth.waitForTransactionReceipt(tx_hash)

class Setup(object):

    def get_api_token(self, email, password):
        r = requests.post(url=self.api_host + 'auth/request_api_token/',
                          headers=dict(Accept='application/json'),
                          json={
                              'email': email,
                              'password': password
                          })

        return r.json()['auth_token']

    def register_blockchain_token(self,
                                  address='0xc4375b7de8af5a38a93548eb8453a498222c4ff2',
                                  name=None,
                                  symbol=None,
                                  exchange_contract_address=None):
        r = requests.post(url=self.api_host + 'token/',
                          headers=dict(Authorization=self.api_token, Accept='application/json'),
                          json={
                              'address': address,
                              'name':  name,
                              'symbol': symbol,
                          })

        token_id = r.json()['data']['token']['id']

        if exchange_contract_address:
            e = requests.put(url=f"{self.api_host}token/{token_id}/exchange_contracts",
                              headers=dict(Authorization=self.api_token, Accept='application/json'),
                              json={'exchange_contract_address': exchange_contract_address})

            resp = e.json()


        return token_id

        return r.json()['data']['organisation']['id']

    def bind_this_user_to_organisation(self, organisation_id):
        u = requests.get(url=self.api_host + 'me/',
                         headers=dict(Authorization=self.api_token, Accept='application/json'))

        user_id = u.json()['data']['user']['id']

        r = requests.put(url=self.api_host + 'organisation/' + str(organisation_id) + '/users',
                         headers=dict(Authorization=self.api_token, Accept='application/json'),
                         json={
                             'user_ids': [user_id]
                         })

        return r.json()['data']['organisation']


    def test_exchange(self, from_token_id, to_token_id, from_amount):

        r = requests.post(url=self.api_host + 'me/exchange/',
                         headers=dict(Authorization=self.api_token, Accept='application/json'),
                         json={
                             'from_token_id': from_token_id,
                             'to_token_id': to_token_id,
                             'from_amount': from_amount
                         })

        json = r.json()

        return json

    def deploy_contracts(self):

        r = requests.post(url=self.api_host + 'contracts/',
                          headers=dict(Authorization=self.api_token, Accept='application/json'),
                          json={
                          })

        return r.json()

    def create_exchange_contract(self):

        tokens_get = requests.get(
            url=self.api_host + 'contract/token/',
            headers=dict(Authorization=self.api_token, Accept='application/json'))

        tokens_resp = tokens_get.json()

        reserve_token_id = None
        for token in tokens_resp['data']['tokens']:
            addr = token['address']
            if addr == config.RESERVE_TOKEN_ADDRESS:
                reserve_token_id = token['id']

        if reserve_token_id is None:
            raise Exception('Reserve token not found')

        exchange_post = requests.post(
            url=self.api_host + 'contract/exchange/',
            headers=dict(Authorization=self.api_token, Accept='application/json'),
            json={
                'reserve_token_id': reserve_token_id
            })

        json = exchange_post.json()
        exchange_contract_id = json['data']['exchange_contract']['id']

        print(f'Exchange contract id: {exchange_contract_id}')

        found = False
        attempts = 0

        while not found and attempts < 100:
            exchange_get = requests.get(
                url=self.api_host + 'contract/exchange/' + str(exchange_contract_id),
                headers=dict(Authorization=self.api_token, Accept='application/json'))

            exchange_get_json = exchange_get.json()

            contract = exchange_get_json['data']['exchange_contract']
            if contract['contract_registry_blockchain_address']:
                found = True

            sleep(5)

        if not found:
            raise TimeoutError

        return exchange_contract_id

    def create_cic_token(
            self,
            exchange_contract_id,
            name,
            symbol,
            issue_amount_wei,
            reserve_deposit_wei,
            reserve_ratio_ppm
    ):

        cic_post = requests.post(
            url=self.api_host + 'contract/token/',
            headers=dict(Authorization=self.api_token, Accept='application/json'),
            json={
                'exchange_contract_id': exchange_contract_id,
                'name': name,
                'symbol': symbol,
                'issue_amount_wei': issue_amount_wei,
                'reserve_deposit_wei': reserve_deposit_wei,
                'reserve_ratio_ppm': reserve_ratio_ppm
            })

        json = cic_post.json()
        token_id = json['data']['token']['id']

        print(f'CIC Token id: {token_id}')

        found = False
        attempts = 0

        while not found and attempts < 100:
            token_get = requests.get(
                url=self.api_host + 'contract/token/' + str(exchange_contract_id),
                headers=dict(Authorization=self.api_token, Accept='application/json'))

            token_get_json = token_get.json()

            contract = token_get_json['data']['token']
            if contract['blockchain_address']:
                found = True

            sleep(5)

        if not found:
            raise TimeoutError

        return exchange_contract_id

    def create_organisation(self, name, token_id):

        r = requests.post(url=self.api_host + 'organisation/',
                          headers=dict(Authorization=self.api_token, Accept='application/json'),
                          json={
                              'token_id': token_id,
                              'name': name
                          })

        return r.json()['data']['organisation']['id']



    def __init__(self, email=None, password=None, api_token=None):

        self.api_host = 'http://0.0.0.0:9000/api/v1/'

        if (email and password):
            self.api_token = self.get_api_token(email, password)
            print("API TOKEN:")
            print(self.api_token)
        elif api_token:
            self.api_token = api_token
        else:
            raise Exception("Must provide either username and password OR api token")


if __name__ == '__main__':

    s = Setup(api_token=
              'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1NzY1NzkyOTMsImlhdCI6MTU3NTk3NDQ5MywiaWQiOjEsInJvbGVzIjp7IkFETUlOIjoic2VtcG9hZG1pbiJ9fQ.7Rw_uMJNLBlDV48oAt5FCDytGbEzcNrCsN5sh1Wc-e4|eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1NzU5NDk5NjUsImlhdCI6MTU3NTg2MzUzNSwiaWQiOjE1fQ.RT2LosnAhthvMzEvY_7a_a_biJoycQEVoHiLw6LhYZk'
    )

    exchange_contract_id = s.create_exchange_contract()

    cic_id = s.create_cic_token(
        exchange_contract_id=exchange_contract_id,
        name='Sarafu',
        symbol='Sarafu',
        issue_amount_wei=int(1e16),
        reserve_deposit_wei=int(1e16),
        reserve_ratio_ppm=250000
    )

    # org_id = s.create_organisation('Foo', 1)


    ttt = 4

    # reserve_token_id = result['data']['reserve_token']['id']
    # cic1_token_id = result['data']['smart_token']['id']
    # cic2_token_id = result['data']['smart_token_2']['id']
    #
    #
    # x = s.test_exchange(reserve_token_id, cic1_token_id, 5*10**-8)
    #
    # y = s.test_exchange(cic1_token_id, cic2_token_id, 1*10**-14)
    #
    # z = s.test_exchange(cic1_token_id, reserve_token_id, 1*10**-14)
    #
    #
    # tt = 5
    #
    # # reserve_token_id = s.register_blockchain_token(
    # #     address=config.RESERVE_TOKEN_ADDRESS,
    # #     name='RESERVE',
    # #     symbol='RSRV')
    # #
    # # cic1_token_id = s.register_blockchain_token('0xA1678D3ED0fF92C66753472e3A015a16DEA0F10f',
    # #                                             name='CIC1',
    # #                                             symbol='CIC1',
    # #                                             exchange_contract_address=config.EXCHANGE_CONTRACT_ADDRESS)
    #
    # # cic2_token_id = s.register_blockchain_token('0x5CB40AcCE23D33fB28015DFf0C552E4583633996',
    # #                                             name='CIC2',
    # #                                             symbol='CIC2',
    # #                                             exchange_contract_address=config.EXCHANGE_CONTRACT_ADDRESS)
    # #
    # # org_id = s.create_organisation('Sempo19', reserve_token_id)
    # # bind_response = s.bind_this_user_to_organisation(org_id)
    # #
    # # print('Bound user to organisation with org level blockchain address {}'.format(bind_response['org_blockchain_address']))
    # #
