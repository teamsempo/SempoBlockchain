import pytest, json, config, base64

from server import bt

from helpers.utils import will_func_test_blockchain

@pytest.mark.parametrize("contract_address, contract_type, filter_type, filter_parameters, status_code", [
    (config.ETH_CONTRACT_ADDRESS, "ERC20", 'TRANSFER', None, 201),
])
def test_sync_filter_api(test_client, create_ip_address, authed_sempo_admin_user, contract_address, contract_type, filter_type, filter_parameters, status_code):
    authed_sempo_admin_user.is_activated = True
    auth_token = authed_sempo_admin_user.encode_auth_token().decode()

    response = test_client.post(
        '/api/v1/synchronization_filter/',
        headers=dict(
            Authorization=auth_token,
            Accept='application/json'
        ),
        json={
            'contract_address': config.ETH_CONTRACT_ADDRESS,
            'contract_type': contract_type,
            'filter_type': filter_type,
            'filter_parameters': filter_parameters
        })


    if status_code == 201 and will_func_test_blockchain():
        task_uuid = response.json['data']['exchange']['blockchain_task_uuid']
        result = bt.await_task_success(task_uuid, timeout=config.SYNCRONOUS_TASK_TIMEOUT * 48)
        assert response.status_code == status_code
        assert result['status'] == 'SUCCESS'
        assert response.json['contract_address'] == contract_address
        assert response.json['contract_type'] == contract_type
        assert response.json['filter_parameters'] == filter_parameters
        assert response.json['filter_type'] == filter_type
