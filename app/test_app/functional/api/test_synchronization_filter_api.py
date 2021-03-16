import pytest, json, config, base64

from server import bt

@pytest.mark.parametrize("contract_address, contract_type, filter_type, filter_parameters, status_code", [
    (config.CHAINS['ETHEREUM']['CONTRACT_ADDRESS'], "ERC20", 'TRANSFER', None, 201),
])
def test_sync_filter_api(test_client, create_ip_address, complete_admin_auth_token, contract_address, contract_type, filter_type, filter_parameters, status_code):
    # Super basic test for creation of sync filters
    # sync_filter_api is very basic right now, but there is added complexity on the roadmap
    response = test_client.post(
        '/api/v1/synchronization_filter/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
        json={
            'call': 'add_transaction_filter',
            'contract_address': config.ETH_CONTRACT_ADDRESS,
            'contract_type': contract_type,
            'filter_type': filter_type,
            'filter_parameters': filter_parameters
        })

    assert response.json['contract_address'] == contract_address
    assert response.json['contract_type'] == contract_type
    assert response.json['filter_parameters'] == filter_parameters
    assert response.json['filter_type'] == filter_type
    assert response.status_code == 201

def test_refetch_block_range_api(test_client, complete_admin_auth_token):
    response = test_client.post(
        '/api/v1/synchronization_filter/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
        json={
            'call': 'refetch_block_range',
            'filter_address': config.ETH_CONTRACT_ADDRESS,
            'floor': '1',
            'ceiling': '100',
        })

    assert response.status_code == 201

def test_force_recall_webhook(test_client, complete_admin_auth_token):
    response = test_client.post(
        '/api/v1/synchronization_filter/',
        headers=dict(
            Authorization=complete_admin_auth_token,
            Accept='application/json'
        ),
        json={
            'call': 'force_recall_webhook',
            'transaction_hash': '0xdeadbeef2322d396649ed2fa2b7e0a944474b65cfab2c4b1435c81bb16697ecb',
        })

    assert response.status_code == 201
