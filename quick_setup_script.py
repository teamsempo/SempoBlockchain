import requests
import config

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

    def create_organisation(self, name, token_id):

        r = requests.post(url=self.api_host + 'organisation/',
                          headers=dict(Authorization=self.api_token, Accept='application/json'),
                          json={
                              'token_id': token_id,
                              'name': name
                          })

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



    def __init__(self, email=None, password=None, api_token=None):

        self.api_host = 'http://0.0.0.0:9000/api/'

        if (email and password):
            self.api_token = self.get_api_token(email, password)
        elif api_token:
            self.api_token = api_token
        else:
            raise Exception("Must provide either username and password OR api token")


if __name__ == '__main__':

    s = Setup(api_token='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1NzIxNzI1ODQsImlhdCI6MTU3MTU2Nzc4NCwiaWQiOjQsInJvbGVzIjp7IkFETUlOIjoic2VtcG9hZG1pbiJ9fQ.BGb3ZUS4Qhq9yh7mqtntiF44MpJhOBFou08O2bvJhjo|eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1NjY1NDU1MDYsImlhdCI6MTU2NjQ1OTA3NiwidXNlcl9pZCI6N30.fNPfyzLfAkONNjERuW8CMIM5QFTz5sC2Ksq87kOz7qM')

    reserve_token_id = s.register_blockchain_token(
        address=config.RESERVE_TOKEN_ADDRESS,
        name='RESERVE',
        symbol='RSRV')

    cic1_token_id = s.register_blockchain_token('0xA1678D3ED0fF92C66753472e3A015a16DEA0F10f',
                                                name='CIC1',
                                                symbol='CIC1',
                                                exchange_contract_address=config.EXCHANGE_CONTRACT_ADDRESS)

    cic2_token_id = s.register_blockchain_token('0x5CB40AcCE23D33fB28015DFf0C552E4583633996',
                                                name='CIC2',
                                                symbol='CIC2',
                                                exchange_contract_address=config.EXCHANGE_CONTRACT_ADDRESS)

    org_id = s.create_organisation('Sempo19', reserve_token_id)
    bind_response = s.bind_this_user_to_organisation(org_id)

    print('Bound user to organisation with org level blockchain address {}'.format(bind_response['org_blockchain_address']))

    s.test_exchange(reserve_token_id, cic1_token_id, 1000000000000000*10**(-16))
