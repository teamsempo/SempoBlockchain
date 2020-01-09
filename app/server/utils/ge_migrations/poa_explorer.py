# -*- coding: utf-8 -*-


def request(url, delay = 5, retry = 5, timeout = 120):
    '''
    Helper function that wraps the common operations for fetching 
    data from the POA Explorer.

    To deal with the rate limiter we need to space out request.
    The current (Oct. 2018) limit is 10 requests per minute.
    '''
    import os, urllib, json
    from urllib.request import Request, urlopen
    from time import sleep
    from socket import timeout as TimeoutException
    req = Request(url, headers = {'User-Agent': 'Mozilla/5.0'})

    for attempt in range(retry):
        try:
            return json.loads(urlopen(req, timeout=timeout).read())
        except urllib.error.HTTPError as err:
            print(url)
            print(err)
            print(err.code)
            print(err.reason)
            print(err.headers)
            if int(err.code) == 400:
                return None
            print("Attempt %d failed. Retrying in %d s." % (attempt+1, delay))
        except TimeoutException:
            print('socket timed out - URL %s' % url)
        finally:
            sleep(delay)

class POAExplorer:                           
    '''
    This is a wrapper around the POA Explorer REST API.
    '''                           
    def __init__(self, base_url = None):
        self.base_url = base_url if base_url else 'https://blockscout.com/poa/core/api'

    def __url(self, **kwargs):
        args = ['='.join(item) for item in kwargs.items()]        
        return self.base_url + '?' + '&'.join(args)

    def token_balance(self, contract_address, address):
        return request(self.__url(module='account',
                                  action='tokenbalance',
                                  contractaddress=contract_address,
                                  address=address))
        
    def balance(self, address):
        '''
        address can be either a single wallet ID or a list of wallet IDs.
        '''
        if isinstance(address, list):
            from math import ceil
            max_add = 20
            n_elements = len(address)
            n_blocks = ceil(len(address)/max_add)
            result = {'result': list(),
                      'status': 1,
                      'message': "Don't ski alone."}
            for start in range(0, n_elements, max_add):
                stop = min(start + max_add, n_elements)
                address_block = ','.join(address[start:stop])
                print(f'getting addresses {start}-{stop} of {n_elements}')
                try:
                    req_res = request(self.__url(module='account',
                                                 action = 'balancemulti',
                                                 address = address_block))
                    result['result'].extend(req_res['result'])
                except:
                    for wid in address_block.split(','):
                        r = self.balance(wid)
                        balance = r['result'] if r else '0'
                        result['result'].append({'balance': balance, 'account' : wid})
            return result
        else:
            return request(self.__url(module='account',
                                      action = 'balance',
                                      address = address))

    def transaction_list(self, address):
        return request(self.__url(module='account',
                                  action = 'txlist',
                                  address = address))

    def get_block(self, address):
        return request(self.__url(module='block',
                                action = 'eth_block_number'))
