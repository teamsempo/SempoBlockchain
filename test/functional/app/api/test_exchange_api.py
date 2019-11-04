import pytest, json, config, base64
import pyotp

from server.utils.auth import get_complete_auth_token
from server import bt

@pytest.mark.parametrize("from_token, to_token, from_amount, status_code", [
    ("smart_token_2", "smart_token_1", 1e5, 400),
    ("reserve_token", "smart_token_1", 1e2, 200),
    ("smart_token_1", "reserve_token", 1e-10, 200),
    ("smart_token_1", "smart_token_2", 1e-10, 200),
])
def test_exchange(test_client, user_with_reserve_balance, initialised_blockchain_network,
                  from_token, to_token, from_amount, status_code):

    from_token_obj = initialised_blockchain_network[from_token]
    to_token_obj = initialised_blockchain_network[to_token]

    response = test_client.post('/api/me/exchange/',
                         headers=dict(
                             Authorization=get_complete_auth_token(user_with_reserve_balance),
                             Accept='application/json'
                         ),
                         json={
                             'from_token_id': from_token_obj.id,
                             'to_token_id': to_token_obj.id,
                             'from_amount': from_amount
                         })

    assert response.status_code == status_code
    if status_code == 200:
        task_id = response.json['data']['exchange']['blockchain_task_id']
        result = bt.await_task_success(task_id, timeout=config.SYNCRONOUS_TASK_TIMEOUT * 15)
        assert result['status'] == 'SUCCESS'
