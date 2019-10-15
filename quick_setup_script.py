import requests


class Setup(object):

    def get_api_token(self, email, password):
        r = requests.post(url=self.api_host + 'auth/request_api_token/',
                          headers=dict(Accept='application/json'),
                          json={
                              'email': email,
                              'password': password
                          })

        return r.json()['auth_token']

    def create_blockchain_token(self):
        r = requests.post(url=self.api_host + 'token/',
                          headers=dict(Authorization=self.api_token, Accept='application/json'),
                          json={
                              'address': '0xc4375b7de8af5a38a93548eb8453a498222c4ff2',
                              'name': 'Kovan DAI',
                              'symbol': 'DAI'
                          })

        return r.json()['data']['token']['id']

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



    def __init__(self, email=None, password=None, api_token=None):

        self.api_host = 'http://0.0.0.0:9000/api/'

        if (email and password):
            self.api_token = self.get_api_token(email, password)
        elif api_token:
            self.api_token = api_token
        else:
            raise Exception("Must provide either username and password OR api token")


if __name__ == '__main__':

    s = Setup(email='test@sempo.ai', password='password')

    token_id = s.create_blockchain_token()
    org_id = s.create_organisation('Sempo14', token_id)
    bind_response = s.bind_this_user_to_organisation(org_id)

    print('Bound user to organisation with org level blockchain address {}'.format(bind_response['org_blockchain_address']))
