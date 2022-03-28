from functools import reduce
import requests
from time import sleep
import os, sys
from json import JSONDecodeError
sys.path.append('./')
import config

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

        self._wait_for_get_result(f'contract/token/{token_id}/', ('data', 'token', 'address'))
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
                'reserve_ratio_ppm': reserve_ratio_ppm,
                'allow_autotopup': True
            })

        json = cic_post.json()
        token_id = json['data']['token_id']

        print(f'CIC Token id: {token_id}')

        self._wait_for_get_result(f'contract/token/{token_id}', ('data', 'token', 'address'))

        return token_id

    def create_cic_organisation(
            self,
            organisation_name,
            custom_welcome_message_key,
            timezone,
            country_code,
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
                              'custom_welcome_message_key': custom_welcome_message_key,
                              'timezone': timezone,
                              'country_code': country_code,
                              'exchange_contract_id': exchange_contract_id,
                              'name': name,
                              'symbol': symbol,
                              'issue_amount_wei': issue_amount_wei,
                              'reserve_deposit_wei': reserve_deposit_wei,
                              'reserve_ratio_ppm': reserve_ratio_ppm,
                              'allow_autotopup': True
                          })

        try:
            json = r.json()

            token_id = json['data']['token_id']
            print(f'{name} Token id: {token_id}')
        except KeyError:
            raise Exception(str(json))

        except JSONDecodeError:
            raise Exception(str(r))


        self._wait_for_get_result(f'contract/token/{token_id}', ('data', 'token', 'address'))

        print(json)

        return json['data']['organisation']['id']

    def create_organisation(self, organisation_name, token_id):

        r = requests.post(url=self.api_host + 'organisation/',
                          headers=dict(Authorization=self.api_token, Accept='application/json'),
                          json={
                              'token_id': token_id,
                              'organisation_name': organisation_name,
                              'country_code': 'AU'
                          })

        return r.json()['data']['organisation']['id']

    def bind_me_to_organisation_as_admin(self, organisation_id):
        u = requests.get(url=self.api_host + 'me/',
                         headers=dict(Authorization=self.api_token, Accept='application/json'))

        user_id = u.json()['data']['user']['id']

        self.bind_user_to_organsation_as_admin(user_id, organisation_id)


    def bind_user_to_organsation_as_admin(self, user_id, organisation_id):

        r = requests.put(url=self.api_host + 'organisation/' + str(organisation_id) + '/users/',
                         headers=dict(Authorization=self.api_token, Accept='application/json'),
                         json={
                             'user_ids': [user_id],
                             'is_admin': True
                         })

        return r.json()['data']['organisation']

    def ussd_request(self, organisation_name, token_id):

        r = requests.post(url=self.api_host + 'ussd',
                          headers=dict(Authorization=self.api_token, Accept='application/json'),
                          json={
                              'token_id': token_id,
                              'organisation_name': organisation_name
                          })

        return r.json()['data']['organisation']['id']

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

def _base_setup(s, reserve_token_id):
    exchange_contract_id = s.create_exchange_contract(reserve_token_id)
    # exchange_contract_id = 1

    org_id = s.create_cic_organisation(
        organisation_name='ACME Org',
        custom_welcome_message_key='custom',
        timezone='Australia/Melbourne',
        country_code='AU',
        exchange_contract_id=exchange_contract_id,
        name='ACME',
        symbol='ACME',
        issue_amount_wei=int(10000000e18),
        reserve_deposit_wei=int(100000e18),
        reserve_ratio_ppm=250000
    )

    bind_1 = s.bind_me_to_organisation_as_admin(org_id)

def local_setup():
    s = Setup(
        api_host='http://0.0.0.0:9000/api/v1/',
        email=os.environ.get('LOCAL_EMAIL', 'admin@acme.org'),
        password=os.environ.get('LOCAL_PASSWORD', 'C0rrectH0rse')
    )

    reserve_token_id = s.create_reserve_token(
        name='Reserve Currency',
        symbol='RCU',
        fund_amount_wei=int(200000e18)
    )

    _base_setup(s, reserve_token_id)

if __name__ == '__main__':

    local_setup()