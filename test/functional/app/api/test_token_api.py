"""
This file (test_token_api.py) contains the functional tests for the token blueprint.

These tests use GETs and POSTs to different URLs to check for the proper behavior
of the token blueprint.
"""
import json, pytest


@pytest.mark.parametrize("status_code", [
    (201)
])
def test_create_token(test_client, complete_admin_auth_token, initialised_blockchain_network, status_code):
    exchange_contract_id = initialised_blockchain_network['exchange_contract'].id

    response = test_client.post('/api/contract/token/',
                               headers=dict(Authorization=complete_admin_auth_token, Accept='application/json'),
                               json={'deploy_smart_token_contract': True,
                                     'exchange_contract_id': exchange_contract_id,
                                     'issue_amount_wei': 1000,
                                     'reserve_deposit_wei': 10,
                                     'reserve_ratio_ppm': 250000,
                                     'name': 'FOO Token',
                                     'symbol': 'FOO'},
                               follow_redirects=True)

    assert response.status_code == status_code