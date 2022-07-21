from server.utils.auth import get_complete_auth_token
import pytest
from flask import g

@pytest.mark.parametrize("data, expected_response_code, expected_response", [
    ({'recipient_blockchain_address': '0x4Cb79e45A25e7cD8004793e593dAC4212bE3c9E4', 'transfer_amount': 1234}, 201, {}),
    ({'recipient_blockchain_address': '0x4Cb79e45A25e7cD8004793e593dAC4212bE3c9E4', 'transfer_amount': '0'}, 201, {}),
    ({'recipient_blockchain_address': '1234'}, 400, {'message': '"transfer_amount" parameter required'}),
    ({'transfer_amount': 1234}, 400, {'message': '"recipient_blockchain_address" parameter required'})
])
def test_create_bulk_credit_transfer(test_client, authed_sempo_admin_user, data, expected_response_code, expected_response):
    authed_sempo_admin_user.default_organisation.org_level_transfer_account._balance_offset_wei = int(100e18)
    authed_sempo_admin_user.default_organisation.org_level_transfer_account.update_balance()
    # Create admin user and auth
    authed_sempo_admin_user.set_held_role('ADMIN', 'superadmin')
    auth = get_complete_auth_token(authed_sempo_admin_user)
    response = test_client.post(
        f"/api/v1/master_wallet/",
        headers=dict(
            Authorization=auth,
            Accept='application/json',
        ),
        json=data
    )
    assert response.status_code == expected_response_code
    
    if response.status_code != 201:
        assert response.json == expected_response
    else:
        assert response.json['data']['credit_transfer'][0]['recipient_transfer_account']['balance'] == 1234
        assert response.json['data']['credit_transfer'][0]['recipient_transfer_account']['blockchain_address'] == '0x4Cb79e45A25e7cD8004793e593dAC4212bE3c9E4'
        assert response.json['data']['credit_transfer'][0]['sender_transfer_account']['id'] == authed_sempo_admin_user.default_organisation.org_level_transfer_account.id
