from functools import reduce
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


    def _wait_for_get_result(self, get_endpoint, check_reference):
        attempts = 300
        for i in range(0, attempts):
            get_response = requests.get(
                url=self.api_host + get_endpoint,
                headers=dict(Authorization=self.api_token, Accept='application/json'))

            json = get_response.json()

            res = reduce(lambda d, r: d.get(r), check_reference, json)

            if res:
                return res

            sleep(5)

        raise TimeoutError

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

    def create_reserve_token(
            self,
            name,
            symbol,
            fund_amount_wei
    ):

        reserve_post = requests.post(
            url=self.api_host + 'contract/token/reserve/',
            headers=dict(Authorization=self.api_token, Accept='application/json'),
            json=dict(
                name=name,
                symbol=symbol,
                fund_amount_wei=fund_amount_wei)
        )

        json = reserve_post.json()
        token_id = json['data']['reserve_token_id']

        print(f'Reserve Token id: {token_id}')

        self._wait_for_get_result(f'contract/token/{token_id}', ('data', 'token', 'address'))

        return token_id

    def create_exchange_contract(self, reserve_token_id):

        exchange_post = requests.post(
            url=self.api_host + 'contract/exchange/',
            headers=dict(Authorization=self.api_token, Accept='application/json'),
            json={
                'reserve_token_id': reserve_token_id
            })

        json = exchange_post.json()
        exchange_contract_id = json['data']['exchange_contract']['id']

        print(f'Exchange contract id: {exchange_contract_id}')

        self._wait_for_get_result(
            f'contract/exchange/{exchange_contract_id}',
            ('data', 'exchange_contract', 'contract_registry_blockchain_address')
        )

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
        token_id = json['data']['token_id']

        print(f'CIC Token id: {token_id}')

        self._wait_for_get_result(f'contract/token/{token_id}', ('data', 'token', 'address'))

        return token_id

    def create_cic_organisation(
            self,
            organisation_name,
            exchange_contract_id,
            name,
            symbol,
            issue_amount_wei,
            reserve_deposit_wei,
            reserve_ratio_ppm
    ):

        r = requests.post(url=self.api_host + 'organisation/',
                          headers=dict(Authorization=self.api_token, Accept='application/json'),
                          json={
                              'deploy_cic': True,
                              'organisation_name': organisation_name,
                              'exchange_contract_id': exchange_contract_id,
                              'name': name,
                              'symbol': symbol,
                              'issue_amount_wei': issue_amount_wei,
                              'reserve_deposit_wei': reserve_deposit_wei,
                              'reserve_ratio_ppm': reserve_ratio_ppm
                          })

        json = r.json()
        try:
            token_id = json['data']['token_id']
            print(f'{name} Token id: {token_id}')
        except KeyError:
            raise Exception(str(json))

        self._wait_for_get_result(f'contract/token/{token_id}', ('data', 'token', 'address'))

        print(json)

        return json['data']['organisation']['id']

    def create_organisation(self, organisation_name, token_id):

        r = requests.post(url=self.api_host + 'organisation/',
                          headers=dict(Authorization=self.api_token, Accept='application/json'),
                          json={
                              'token_id': token_id,
                              'organisation_name': organisation_name
                          })

        return r.json()['data']['organisation']['id']

    def bind_me_to_organisation_as_admin(self, organisation_id):
        u = requests.get(url=self.api_host + 'me/',
                         headers=dict(Authorization=self.api_token, Accept='application/json'))

        user_id = u.json()['data']['user']['id']

        self.bind_user_to_organsation_as_admin(user_id, organisation_id)


    def bind_user_to_organsation_as_admin(self, user_id, organisation_id):

        r = requests.put(url=self.api_host + 'organisation/' + str(organisation_id) + '/users',
                         headers=dict(Authorization=self.api_token, Accept='application/json'),
                         json={
                             'user_ids': [user_id],
                             'is_admin': True
                         })

        return r.json()['data']['organisation']

    def __init__(self, api_host='http://0.0.0.0:9000/api/v1/', email=None, password=None, api_token=None):

        self.api_host = api_host

        if email and password:
            self.api_token = self.get_api_token(email, password)
            print("API TOKEN:")
            print(self.api_token)
        elif api_token:
            self.api_token = api_token
        else:
            raise Exception("Must provide either username and password OR api token")


if __name__ == '__main__':

    s = Setup(
        api_host='https://dev.withsempo.com/api/v1/',
        api_token=
        'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1NzcxODU3NzQsImlhdCI6MTU3NjU4MDk3NCwiaWQiOjEsInJvbGVzIjp7IkFETUlOIjoic2VtcG9hZG1pbiJ9fQ.CGrSHCUcpJlGq3sBgim7omwTBZAx-v0N3AAUurlkqhI|eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjI0Mzk2MDQxMjYsImlhdCI6MTU3NTY5MDQ5NiwiaWQiOjJ9.WaSdLvU5aGxLmNo5uZV0_PmV7LOTymeBBxOymy0Er7U'
    )

    # s = Setup(
    #     api_host='http://0.0.0.0:9000/api/v1/',
    #     api_token=
    #     'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1NzcxNjc3MDgsImlhdCI6MTU3NjU2MjkwOCwiaWQiOjEsInJvbGVzIjp7IkFETUlOIjoic2VtcG9hZG1pbiJ9fQ.S1dMa668pSLkbNAYzgWOC6Td-E84xgDxEg5ilinKiGI|eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1NzYyMTEzMDIsImlhdCI6MTU3NjEyNDg3MiwiaWQiOjZ9.zkEUtwMgOSrcLy68Rtv_JeMCj9HrsOyQUfH3Dc3itYE'
    # )
    # #


    # s.bind_user_to_organsation_as_admin(6, 1)
    # s.bind_user_to_organsation_as_admin(6, 2)
    # s.bind_user_to_organsation_as_admin(6, 3)


    # reserve_token_id = s.create_reserve_token(
    #     name='Kenyan Shilling',
    #     symbol='Ksh',
    #     fund_amount_wei=int(1000e18)
    # )
    reserve_token_id = 1

    exchange_contract_id = s.create_exchange_contract(reserve_token_id)
    # exchange_contract_id = 4

    ge_org_id = s.create_cic_organisation(
        organisation_name='Grassroots Economics',
        exchange_contract_id=exchange_contract_id,
        name='Sarafu',
        symbol='SAR',
        issue_amount_wei=int(1000e18),
        reserve_deposit_wei=int(10e18),
        reserve_ratio_ppm=250000
    )
    bind_1 = s.bind_me_to_organisation_as_admin(ge_org_id)

    foobar_org_id = s.create_cic_organisation(
        organisation_name='Foo Org',
        exchange_contract_id=exchange_contract_id,
        name='FooBar',
        symbol='FOO',
        issue_amount_wei=int(1000e18),
        reserve_deposit_wei=int(10e18),
        reserve_ratio_ppm=250000
    )
    bind_2 = s.bind_me_to_organisation_as_admin(foobar_org_id)

    tt = 4
